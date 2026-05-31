"""Remote LightRAG status reconciler sketch."""


class RemoteStatusReconciler:
    def __init__(self, document_repo, operation_repo, lightrag_client_factory, status_service):
        self.document_repo = document_repo
        self.operation_repo = operation_repo
        self.lightrag_client_factory = lightrag_client_factory
        self.status_service = status_service

    async def reconcile_document(self, document_id: str) -> None:
        document = await self.document_repo.get(document_id)
        if document is None:
            return

        operation = await self.operation_repo.get_latest_for_resource("document", document_id, kind="document_ingest")
        if operation is None:
            return

        # Only reconcile active/waiting work.
        if operation.status not in {"queued", "running"}:
            return

        remote_status = await self._fetch_remote_status(document)
        mapped = self._map_remote_status(remote_status)

        if mapped == "ready":
            await self.status_service.mark_succeeded(document_id, operation.id)
        elif mapped == "failed":
            await self.status_service.mark_failed(document_id, operation.id, error_message="LightRAG indexing failed")
        elif mapped == "indexing":
            await self.status_service.mark_waiting_remote(
                document_id,
                operation.id,
                message="Waiting for LightRAG to finish indexing",
            )
        # Unknown/unavailable: preserve local state and record diagnostic only.

    async def _fetch_remote_status(self, document):
        raise NotImplementedError

    def _map_remote_status(self, remote_status: str) -> str:
        value = (remote_status or "").lower()
        if value in {"ready", "processed", "complete", "completed", "success", "succeeded"}:
            return "ready"
        if value in {"failed", "error", "errored"}:
            return "failed"
        if value in {"pending", "queued", "processing", "parsing", "analyzing", "indexing"}:
            return "indexing"
        return "unknown"
