from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.models import DocumentStatus
from app.integrations.lightrag_remote_adapter import LightRAGRemoteAdapter
from app.storage.repositories.documents import DocumentRepository


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
        now: Callable[[], datetime] | None = None,
    ):
        self.documents = DocumentRepository(session)
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
            remote = adapter.upload_document(
                file_path=Path(document.storage_path),
                filename=document.filename,
                content_type=document.content_type,
                metadata={"local_document_id": document.id},
                domain=str(domain_id),
            )
            status = str(remote.get("status") or "indexing")
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
        finally:
            lock.release()
