from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.models import DocumentStatus
from app.schemas.documents import (
    DomainDocumentsProcessingStatusResponse,
    ProcessingDiagnostics,
    ProcessingDocumentStatus,
    ProcessingDomainStatus,
    ProcessingStatusResponse,
)
from app.storage.repositories.jobs import JobRepository
from app.storage.tables import DocumentRow, JobRow


ACTIVE_DOCUMENT_STATUSES = {DocumentStatus.UPLOADED.value, DocumentStatus.INDEXING.value}
ACTIVE_OPERATION_STATUSES = {"queued", "running"}


class ProcessingStatusService:
    """Compose the upload processing read model without mutating state."""

    def __init__(self, session: Session):
        self.jobs = JobRepository(session)

    def for_document(self, document: DocumentRow) -> ProcessingStatusResponse:
        operation = self._latest_operation(document.id)
        document_status = self._document_status(document, operation)
        return ProcessingStatusResponse(
            document=document_status,
            domain=self._domain_status(document, [document_status]),
            diagnostics=self._diagnostics(document),
        )

    def for_domain_documents(
        self, *, domain_id: str, documents: list[DocumentRow]
    ) -> DomainDocumentsProcessingStatusResponse:
        operations = self._latest_operations_by_document_id([document.id for document in documents])
        rows = [
            self._document_status(document, operations.get(document.id))
            for document in documents
        ]
        return DomainDocumentsProcessingStatusResponse(
            domain=ProcessingDomainStatus(domain_id=domain_id, is_busy=any(row_is_busy(row) for row in rows)),
            documents=rows,
        )

    def domain_summary(self, *, domain_id: str, documents: list[DocumentRow]) -> ProcessingDomainStatus:
        rows = self.for_domain_documents(domain_id=domain_id, documents=documents).documents
        return ProcessingDomainStatus(domain_id=domain_id, is_busy=any(row_is_busy(row) for row in rows))

    def _latest_operation(self, document_id: str) -> JobRow | None:
        return self._latest_operations_by_document_id([document_id]).get(document_id)

    def _latest_operations_by_document_id(self, document_ids: list[str]) -> dict[str, JobRow]:
        latest: dict[str, JobRow] = {}
        for job in self.jobs.list_by_document_ids(document_ids):
            if job.document_id and job.document_id not in latest:
                latest[job.document_id] = job
        return latest

    def _document_status(self, document: DocumentRow, operation: JobRow | None) -> ProcessingDocumentStatus:
        operation_updated_at = operation.updated_at if operation is not None else None
        updated_at = max_datetime(document.updated_at, operation_updated_at)
        return ProcessingDocumentStatus(
            document_id=document.id,
            filename=document.filename,
            status=document.status,
            stage=self._stage(document, operation),
            message=self._message(document, operation),
            can_retry=document.status == DocumentStatus.FAILED.value,
            operation_id=operation.id if operation is not None else None,
            operation_status=operation.status if operation is not None else None,
            updated_at=updated_at,
        )

    def _domain_status(
        self, document: DocumentRow, rows: list[ProcessingDocumentStatus]
    ) -> ProcessingDomainStatus:
        return ProcessingDomainStatus(
            domain_id=self._domain_id(document),
            is_busy=any(row_is_busy(row) for row in rows),
        )

    def _diagnostics(self, document: DocumentRow) -> ProcessingDiagnostics:
        lightrag = self._lightrag_metadata(document)
        return ProcessingDiagnostics(
            last_remote_status=lightrag.get("last_remote_status") or lightrag.get("status"),
            last_remote_check_at=lightrag.get("last_remote_check_at")
            or lightrag.get("last_status_check_at"),
        )

    def _stage(self, document: DocumentRow, operation: JobRow | None) -> str | None:
        if operation is not None:
            stage = getattr(operation, "stage", None) or operation.meta.get("stage")
            if stage:
                return str(stage)
            if operation.status == "succeeded":
                return "complete"
            if operation.status == "failed":
                return "failed"
            if operation.status == "queued":
                return "register_upload"
        if document.status == DocumentStatus.READY.value:
            return "complete"
        if document.status == DocumentStatus.FAILED.value:
            return "failed"
        if document.status == DocumentStatus.INDEXING.value:
            return "poll_remote_indexing"
        return None

    def _message(self, document: DocumentRow, operation: JobRow | None) -> str | None:
        if operation is not None:
            message = getattr(operation, "message", None) or operation.meta.get("message")
            if message:
                return str(message)
            if operation.error_message:
                return operation.error_message
        if document.error_message:
            return document.error_message
        lightrag = self._lightrag_metadata(document)
        message = lightrag.get("message")
        return str(message) if message else None

    def _domain_id(self, document: DocumentRow) -> str | None:
        if document.lightrag_domain_id:
            return document.lightrag_domain_id
        lightrag = self._lightrag_metadata(document)
        domain_id = lightrag.get("domain_id") or lightrag.get("domain")
        return str(domain_id) if domain_id else None

    def _lightrag_metadata(self, document: DocumentRow) -> dict:
        metadata = document.meta if isinstance(document.meta, dict) else {}
        lightrag = metadata.get("lightrag", {}) if isinstance(metadata, dict) else {}
        return dict(lightrag) if isinstance(lightrag, dict) else {}


def row_is_busy(row: ProcessingDocumentStatus) -> bool:
    return row.status in ACTIVE_DOCUMENT_STATUSES or row.operation_status in ACTIVE_OPERATION_STATUSES


def max_datetime(first: datetime, second: datetime | None) -> datetime:
    if second is None:
        return first
    return second if second > first else first
