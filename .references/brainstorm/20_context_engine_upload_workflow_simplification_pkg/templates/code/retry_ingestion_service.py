"""Document retry service sketch."""


class DocumentRetryService:
    def __init__(self, document_repo, operation_repo, status_service, queue_service):
        self.document_repo = document_repo
        self.operation_repo = operation_repo
        self.status_service = status_service
        self.queue_service = queue_service

    async def retry_ingestion(self, *, document_id: str, requested_by_user_id: str) -> dict:
        document = await self.document_repo.get(document_id)
        if document is None:
            raise ValueError("Document not found")
        if document.status != "failed":
            raise ValueError("Document is not retryable")

        operation = await self.operation_repo.create(
            kind="document_ingest",
            resource_type="document",
            resource_id=document_id,
            requested_by_user_id=requested_by_user_id,
            status="queued",
            stage="queued",
            message="Queued for retry",
        )
        await self.status_service.mark_queued(document_id, operation.id)
        await self.queue_service.enqueue_document_ingest(operation.id)

        return {
            "document_id": document_id,
            "operation_id": operation.id,
            "status_url": f"/documents/{document_id}/processing-status",
        }
