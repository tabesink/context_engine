from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.domain.models import DocumentStatus, JobStatus
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.jobs import JobRepository


class DocumentIngestionStatusService:
    def __init__(self, session: Session):
        self.documents = DocumentRepository(session)
        self.jobs = JobRepository(session)

    def mark_queued(
        self,
        *,
        document_id: str,
        operation_id: str,
        message: str = "Queued for processing",
    ) -> None:
        document, operation = self._load(document_id, operation_id)
        self.documents.update_status(document, DocumentStatus.INDEXING)
        self.jobs.set_status(
            operation,
            JobStatus.QUEUED,
            stage="queued",
            message=message,
            error_message=None,
        )

    def mark_running(self, *, document_id: str, operation_id: str, stage: str, message: str) -> None:
        document, operation = self._load(document_id, operation_id)
        self.documents.update_status(document, DocumentStatus.INDEXING)
        self.jobs.mark_operation_running(operation, stage=stage, message=message)

    def mark_waiting_remote(self, *, document_id: str, operation_id: str, message: str) -> None:
        self.mark_running(
            document_id=document_id,
            operation_id=operation_id,
            stage="waiting_remote",
            message=message,
        )

    def mark_succeeded(self, *, document_id: str, operation_id: str) -> None:
        document, operation = self._load(document_id, operation_id)
        self.documents.update_status(document, DocumentStatus.READY)
        self.jobs.mark_operation_succeeded(operation, stage="complete", message="Ready")

    def mark_failed(self, *, document_id: str, operation_id: str, error_message: str) -> None:
        document, operation = self._load(document_id, operation_id)
        self.documents.update_status(document, DocumentStatus.FAILED, error_message=error_message)
        self.jobs.mark_operation_failed(
            operation,
            error_message=error_message,
            stage="failed",
            message=error_message,
        )

    def reconcile_remote_status(
        self,
        *,
        document_id: str,
        remote_status: str,
        error_message: str | None = None,
    ) -> None:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        operation = self._latest_operation(document_id)
        if remote_status == "ready":
            self.documents.update_status(document, DocumentStatus.READY)
            if operation is not None:
                self.jobs.mark_operation_succeeded(operation, stage="complete", message="Ready")
            return
        if remote_status == "failed":
            message = error_message or "Document ingestion failed"
            self.documents.update_status(document, DocumentStatus.FAILED, error_message=message)
            if operation is not None:
                self.jobs.mark_operation_failed(
                    operation,
                    error_message=message,
                    stage="failed",
                    message=message,
                )
            return
        if remote_status == "indexing":
            self.documents.update_status(document, DocumentStatus.INDEXING)
            if operation is not None:
                self.jobs.mark_operation_running(
                    operation,
                    stage="waiting_remote",
                    message="Waiting for LightRAG to finish indexing",
                )

    def _latest_operation(self, document_id: str):
        operations = self.jobs.list_by_document_ids([document_id])
        return operations[0] if operations else None

    def _load(self, document_id: str, operation_id: str):
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        operation = self.jobs.get(operation_id)
        if not operation:
            raise not_found("Operation not found")
        return document, operation
