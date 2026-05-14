from fastapi import UploadFile
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

    def upload(self, *, actor_id: str, file: UploadFile) -> tuple[DocumentRow, str | None]:
        if self.settings.lightrag_enabled:
            return self._upload_remote(actor_id=actor_id, file=file)

        path = self.storage.save_upload(file)
        document = self.documents.create(
            owner_id=actor_id,
            filename=file.filename or path.name,
            content_type=file.content_type or "application/octet-stream",
            storage_path=str(path),
            metadata={"original_filename": file.filename},
        )
        self.documents.audit(
            actor_id=actor_id,
            event="document.uploaded",
            target_id=document.id,
            metadata={"filename": document.filename},
        )
        job_id = JobService(self.session).enqueue_index_document(document_id=document.id)
        return document, job_id

    def _upload_remote(self, *, actor_id: str, file: UploadFile) -> tuple[DocumentRow, str | None]:
        path = self.storage.save_upload(file)
        metadata = {
            "original_filename": file.filename,
            "lightrag": {
                "enabled": True,
                "domain": self.settings.lightrag_domain,
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
        try:
            remote = LightRAGRemoteAdapter.for_domain().upload_document(
                file_path=path,
                filename=document.filename,
                content_type=document.content_type,
                metadata={"local_document_id": document.id},
                domain=self.settings.lightrag_domain,
            )
        except LightRAGAdapterError as exc:
            self.documents.update_status(document, DocumentStatus.FAILED, error_message=str(exc))
            raise lightrag_http_exception(exc) from exc

        document = self.documents.update_metadata(
            document,
            metadata
            | {
                "lightrag": metadata["lightrag"]
                | {
                    "document_id": remote.get("document_id"),
                    "track_id": remote.get("track_id"),
                    "status": remote.get("status"),
                    "message": remote.get("message"),
                }
            },
        )
        self.documents.audit(
            actor_id=actor_id,
            event="document.uploaded",
            target_id=document.id,
            metadata={"filename": document.filename, "engine": "lightrag"},
        )
        return document, None

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

