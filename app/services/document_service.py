import json
from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import not_found
from app.domain.models import DocumentStatus
from app.integrations.lightrag_remote_adapter import (
    LightRAGAdapterError,
    LightRAGRemoteAdapter,
    lightrag_http_exception,
)
from app.services.file_storage import FileStorage
from app.services.job_service import JobService
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow


class DocumentService:
    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()
        self.documents = DocumentRepository(session)
        self.storage = FileStorage()

    def upload(
        self,
        *,
        actor_id: str,
        file: UploadFile,
        semantic_engine: str = "lightrag",
        lightrag_domain_id: str | None = None,
    ) -> tuple[DocumentRow, str | None]:
        return self._upload_remote(
            actor_id=actor_id,
            file=file,
            semantic_engine=semantic_engine,
            lightrag_domain_id=lightrag_domain_id,
        )

    def _upload_remote(
        self,
        *,
        actor_id: str,
        file: UploadFile,
        semantic_engine: str = "lightrag",
        lightrag_domain_id: str | None = None,
    ) -> tuple[DocumentRow, str | None]:
        if semantic_engine != "lightrag":
            raise HTTPException(
                status_code=400,
                detail="Only semantic_engine='lightrag' is supported. Local semantic indexing has been removed.",
            )
        domain_id = lightrag_domain_id or self.settings.lightrag_domain
        self._validate_lightrag_domain(domain_id)
        path = self.storage.save_upload(file)
        metadata = {
            "original_filename": file.filename,
            "semantic_engine": "lightrag",
            "lightrag": {
                "enabled": True,
                "domain": domain_id,
                "domain_id": domain_id,
                "status": "queued",
            },
        }
        document = self.documents.create(
            owner_id=actor_id,
            filename=file.filename or path.name,
            content_type=file.content_type or "application/octet-stream",
            storage_path=str(path),
            metadata=metadata,
            status=DocumentStatus.INDEXING,
        )
        jobs = JobService(self.session)
        job_id = jobs.enqueue_lightrag_ingest_document(document_id=document.id)
        self.documents.audit(
            actor_id=actor_id,
            event="document.uploaded",
            target_id=document.id,
            metadata={"filename": document.filename, "engine": "lightrag"},
        )
        return document, job_id

    def _validate_lightrag_domain(self, domain_id: str) -> None:
        path = self.settings.lightrag_domain_manifest or self.settings.lightrag_domains_manifest
        if not path or not path.is_file():
            raise HTTPException(
                status_code=400,
                detail="LightRAG domain manifest is required for uploads.",
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        domains = payload.get("domains", [])
        if isinstance(domains, dict):
            entry = domains.get(domain_id)
        else:
            entry = next(
                (
                    item
                    for item in domains
                    if isinstance(item, dict)
                    and (item.get("id") == domain_id or item.get("name") == domain_id)
                ),
                None,
            )
        if not isinstance(entry, dict):
            raise HTTPException(status_code=400, detail=f"LightRAG domain '{domain_id}' does not exist")
        status = str(entry.get("status") or "").lower()
        if status in {"stopped", "unhealthy", "archived", "error"}:
            raise HTTPException(status_code=400, detail=f"LightRAG domain '{domain_id}' is not available")

    def get_ready_or_404(self, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document or document.status != DocumentStatus.READY.value:
            raise not_found("Document not found")
        return document

    def delete(self, *, actor_id: str, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        self.documents.mark_deleted(document)
        self.documents.audit(
            actor_id=actor_id,
            event="document.deleted",
            target_id=document.id,
            metadata={"filename": document.filename},
        )
        return document

    def refresh_lightrag_status(self, *, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        lightrag = dict(document.meta.get("lightrag") or {})
        domain_id = lightrag.get("domain_id") or lightrag.get("domain")
        track_id = lightrag.get("track_id")
        if not domain_id or not track_id:
            raise HTTPException(status_code=400, detail="Document has no LightRAG track status")
        try:
            status_payload = LightRAGRemoteAdapter.for_domain(str(domain_id)).document_status(str(track_id))
        except LightRAGAdapterError as exc:
            raise lightrag_http_exception(exc) from exc

        status = str(status_payload.get("status") or "")
        if status not in {"indexing", "ready", "failed"}:
            raise HTTPException(status_code=502, detail=f"Unknown LightRAG status: {status!r}")
        updated_lightrag = lightrag | {
            "document_id": status_payload.get("document_id") or lightrag.get("document_id"),
            "track_id": status_payload.get("track_id") or track_id,
            "status": status,
            "message": status_payload.get("error"),
            "last_status_check_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        document = self.documents.update_metadata(
            document,
            document.meta | {"lightrag": updated_lightrag},
        )
        if status == "ready":
            return self.documents.update_status(document, DocumentStatus.READY)
        if status == "failed":
            return self.documents.update_status(
                document,
                DocumentStatus.FAILED,
                error_message=updated_lightrag.get("message"),
            )
        return document

    def refresh_pending_lightrag_statuses(self) -> list[DocumentRow]:
        refreshed: list[DocumentRow] = []
        for document in self.documents.list_lightrag_indexing():
            refreshed.append(self.refresh_lightrag_status(document_id=document.id))
        return refreshed

    def rebuild_structure(
        self,
        *,
        actor_id: str,
        document_id: str,
        preserve_assets: bool = True,
    ) -> str:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        metadata = dict(document.meta or {})
        metadata["document_processing"] = dict(metadata.get("document_processing") or {}) | {
            "preserve_assets": preserve_assets,
        }
        metadata["lightrag"] = dict(metadata.get("lightrag") or {}) | {"status": "queued"}
        document = self.documents.update_metadata(document, metadata)
        self.documents.update_status(document, DocumentStatus.INDEXING)
        self.documents.audit(
            actor_id=actor_id,
            event="document.structure_rebuild_queued",
            target_id=document_id,
            metadata={"preserve_assets": preserve_assets},
        )
        return JobService(self.session).enqueue_lightrag_ingest_document(document_id=document_id)

    def reingest_lightrag(self, *, actor_id: str, document_id: str) -> str:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        metadata = dict(document.meta or {})
        metadata["lightrag"] = dict(metadata.get("lightrag") or {}) | {"status": "queued"}
        document = self.documents.update_metadata(document, metadata)
        self.documents.update_status(document, DocumentStatus.INDEXING)
        self.documents.audit(
            actor_id=actor_id,
            event="document.lightrag_reingest_queued",
            target_id=document_id,
            metadata={},
        )
        return JobService(self.session).enqueue_lightrag_ingest_document(document_id=document_id)

