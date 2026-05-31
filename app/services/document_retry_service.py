from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.domain.models import DocumentStatus
from app.services.document_ingestion_status_service import DocumentIngestionStatusService
from app.services.job_service import JobService
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow


class DocumentRetryService:
    def __init__(self, session: Session):
        self.session = session
        self.documents = DocumentRepository(session)

    def retry_ingestion(self, *, actor_id: str, document_id: str) -> tuple[DocumentRow, str]:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        if document.status != DocumentStatus.FAILED.value:
            raise HTTPException(status_code=400, detail="Document is not retryable")

        metadata = dict(document.meta or {})
        lightrag = dict(metadata.get("lightrag") or {})
        metadata["lightrag"] = lightrag | {"status": "queued"}
        document = self.documents.update_metadata(document, metadata)
        job_id = JobService(self.session).enqueue_document_ingest(
            document_id=document_id,
            requested_by_user_id=actor_id,
        )
        DocumentIngestionStatusService(self.session).mark_queued(
            document_id=document_id,
            operation_id=job_id,
            message="Queued for retry",
        )
        self.documents.audit(
            actor_id=actor_id,
            event="document.retry_ingestion_queued",
            target_id=document_id,
            metadata={},
        )
        self.session.expire_all()
        refreshed = self.documents.get(document_id)
        if not refreshed:
            raise not_found("Document not found")
        return refreshed, job_id
