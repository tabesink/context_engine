"""Processing status presenter sketch.

This layer composes status for UI. It should not own status transitions.
"""


class ProcessingStatusPresenter:
    def __init__(self, document_repo, operation_repo, domain_status_service):
        self.document_repo = document_repo
        self.operation_repo = operation_repo
        self.domain_status_service = domain_status_service

    async def get_document_processing_status(self, document_id: str) -> dict:
        document = await self.document_repo.get(document_id)
        operation = await self.operation_repo.get_latest_for_resource("document", document_id, kind="document_ingest")
        domain = await self.domain_status_service.get_summary(document.lightrag_domain_id)

        return {
            "document": {
                "document_id": document.id,
                "filename": document.filename,
                "status": document.status,
                "stage": getattr(operation, "stage", None) if operation else None,
                "message": self._message(document, operation),
                "can_retry": self._can_retry(document, operation),
                "operation_id": getattr(operation, "id", None) if operation else None,
                "operation_status": getattr(operation, "status", None) if operation else None,
                "updated_at": document.updated_at.isoformat(),
            },
            "domain": domain,
        }

    def _message(self, document, operation) -> str | None:
        if operation and getattr(operation, "message", None):
            return operation.message
        if document.status == "ready":
            return "Ready"
        if document.status == "failed":
            return document.error_message or "Processing failed"
        return None

    def _can_retry(self, document, operation) -> bool:
        return document.status == "failed"
