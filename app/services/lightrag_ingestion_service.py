from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.document_processing.artifacts import DocumentProcessingArtifactStore
from app.document_processing.chunk_builder import StructureAwareChunkBuilder
from app.document_processing.docling_parser import DoclingParser
from app.document_processing.pipeline import TextDoclingParser
from app.document_processing.refinement import StructureQualityScorer, TocRefiner
from app.domain.models import DocumentStatus
from app.integrations.lightrag_remote_adapter import LightRAGRemoteAdapter
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow


class DomainIngestBusy(Exception):
    pass


class IngestLock(Protocol):
    def acquire(self) -> bool:
        ...

    def release(self) -> None:
        ...


class RedisIngestLock:
    def __init__(self, *, domain_id: str, timeout_seconds: int = 1800):
        settings = get_settings()
        self._lock = Redis.from_url(settings.redis_url).lock(
            f"lightrag:domain:{domain_id}:ingest_lock",
            timeout=timeout_seconds,
            blocking=False,
        )

    def acquire(self) -> bool:
        return bool(self._lock.acquire())

    def release(self) -> None:
        try:
            self._lock.release()
        except Exception:
            pass


class LightRAGIngestionService:
    def __init__(
        self,
        session: Session,
        *,
        adapter_factory: Callable[[str], LightRAGRemoteAdapter] | None = None,
        lock_factory: Callable[[str], IngestLock] | None = None,
        structure_parser: TextDoclingParser | None = None,
        chunk_builder: StructureAwareChunkBuilder | None = None,
        quality_scorer: StructureQualityScorer | None = None,
        toc_refiner: TocRefiner | None = None,
        artifact_store: DocumentProcessingArtifactStore | None = None,
        now: Callable[[], datetime] | None = None,
    ):
        self.documents = DocumentRepository(session)
        self.document_processing = DocumentProcessingRepository(session)
        self.structure_parser = structure_parser
        self.text_parser = TextDoclingParser()
        self.docling_parser = DoclingParser()
        self.chunk_builder = chunk_builder or StructureAwareChunkBuilder()
        self.quality_scorer = quality_scorer or StructureQualityScorer()
        self.toc_refiner = toc_refiner or TocRefiner()
        self.artifact_store = artifact_store or DocumentProcessingArtifactStore()
        self.adapter_factory = adapter_factory or LightRAGRemoteAdapter.for_domain
        self.lock_factory = lock_factory or (lambda domain_id: RedisIngestLock(domain_id=domain_id))
        self.now = now or (lambda: datetime.now(UTC))

    def ingest_document(self, document_id: str) -> None:
        document = self.documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        lightrag = dict(document.meta.get("lightrag") or {})
        domain_id = lightrag.get("domain_id") or lightrag.get("domain")
        if not domain_id:
            raise ValueError(f"Document {document_id} has no LightRAG domain")

        lock = self.lock_factory(str(domain_id))
        if not lock.acquire():
            raise DomainIngestBusy(f"LightRAG domain '{domain_id}' is already ingesting")

        try:
            adapter = self.adapter_factory(str(domain_id))
            remote = self._ingest_source_chunks(document=document, adapter=adapter, domain_id=str(domain_id))
            self._apply_remote_status(document=document, lightrag=lightrag, remote=remote, adapter=adapter)
        except Exception as exc:
            self._mark_failed(document=document, lightrag=lightrag, message=str(exc))
            raise
        finally:
            lock.release()

    def _ingest_source_chunks(
        self,
        *,
        document: DocumentRow,
        adapter: LightRAGRemoteAdapter,
        domain_id: str,
    ) -> dict:
        if not self._can_build_document_structure(document):
            raise ValueError(
                f"Document {document.id} cannot be structure-processed for LightRAG ingestion."
            )

        try:
            parser = self.structure_parser or self._parser_for_document(document)
            structure = parser.parse(
                document_id=document.id,
                source_path=Path(document.storage_path),
            )
        except Exception as exc:
            raise ValueError(
                f"Structure-aware ingestion failed for document {document.id}: {exc}"
            ) from exc

        structure = structure.model_copy(update={"quality": self.quality_scorer.score(structure)})
        toc_refinement_mode = self._toc_refinement_mode(document)
        should_refine = toc_refinement_mode == "always" or (
            toc_refinement_mode == "auto" and structure.quality.should_run_toc_refiner
        )
        if should_refine:
            refinement = self.toc_refiner.refine(structure)
            self.document_processing.save_toc_refinement_report(
                document_id=document.id,
                enabled=True,
                result=refinement,
            )
            self.artifact_store.save_toc_refinement_report(
                document_id=document.id,
                enabled=True,
                result=refinement,
            )
            structure = refinement.structure

        structure = self.chunk_builder.build(structure)
        if not structure.source_chunks:
            raise ValueError(
                f"Structure-aware ingestion produced no source chunks for document {document.id}."
            )

        self.document_processing.save_structure(structure)
        self.artifact_store.save_structure(structure)
        return adapter.ingest_source_chunks(domain=domain_id, chunks=structure.source_chunks)

    def _mark_failed(self, *, document: DocumentRow, lightrag: dict, message: str) -> None:
        updated_lightrag = lightrag | {
            "status": "failed",
            "message": message,
            "last_status_check_at": self.now().isoformat().replace("+00:00", "Z"),
        }
        document = self.documents.update_metadata(document, document.meta | {"lightrag": updated_lightrag})
        self.documents.update_status(document, DocumentStatus.FAILED, error_message=message)

    def _can_build_document_structure(self, document: DocumentRow) -> bool:
        content_type = (document.content_type or "").split(";")[0].strip().lower()
        if content_type.startswith("text/"):
            return True
        return Path(document.filename).suffix.lower() in {".md", ".markdown", ".txt", ".pdf"}

    def _parser_for_document(self, document: DocumentRow):
        content_type = (document.content_type or "").split(";")[0].strip().lower()
        suffix = Path(document.filename).suffix.lower()
        if content_type.startswith("text/") or suffix in {".md", ".markdown", ".txt"}:
            return self.text_parser
        return self.docling_parser

    def _toc_refinement_mode(self, document: DocumentRow) -> str:
        metadata = document.meta if isinstance(document.meta, dict) else {}
        processing = metadata.get("document_processing")
        if isinstance(processing, dict) and "enable_toc_refinement" in processing:
            return self._normalize_toc_refinement_mode(processing["enable_toc_refinement"])
        if "enable_toc_refinement" in metadata:
            return self._normalize_toc_refinement_mode(metadata["enable_toc_refinement"])
        return "auto"

    def _normalize_toc_refinement_mode(self, value: object) -> str:
        if isinstance(value, bool):
            return "always" if value else "never"
        mode = str(value or "auto").strip().lower()
        if mode in {"always", "auto", "never"}:
            return mode
        return "auto"

    def _apply_remote_status(
        self,
        *,
        document: DocumentRow,
        lightrag: dict,
        remote: dict,
        adapter: LightRAGRemoteAdapter,
    ) -> None:
        raw_status = remote.get("status")
        if raw_status is None:
            raise ValueError("LightRAG ingestion response missing status.")
        status = str(raw_status)
        track_id = remote.get("track_id")
        if status == "indexing" and track_id:
            status_payload = adapter.document_status(str(track_id))
            status = str(status_payload.get("status") or status)
            remote = remote | status_payload

        updated_lightrag = lightrag | {
            "document_id": remote.get("document_id"),
            "track_id": remote.get("track_id", track_id),
            "status": status,
            "message": remote.get("message") or remote.get("error"),
            "last_status_check_at": self.now().isoformat().replace("+00:00", "Z"),
        }
        document = self.documents.update_metadata(
            document,
            document.meta | {"lightrag": updated_lightrag},
        )
        if status == "ready":
            self.documents.update_status(document, DocumentStatus.READY)
        elif status == "failed":
            self.documents.update_status(
                document,
                DocumentStatus.FAILED,
                error_message=updated_lightrag.get("message"),
            )
        elif status != "indexing":
            raise ValueError(f"Unknown LightRAG status: {status!r}")
