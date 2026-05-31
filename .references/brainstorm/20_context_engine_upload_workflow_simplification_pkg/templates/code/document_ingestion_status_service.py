"""Central status transition service sketch.

All upload/ingestion status transitions should pass through one service like this.
"""

from datetime import datetime, timezone


class DocumentIngestionStatusService:
    def __init__(self, document_repo, operation_repo):
        self.document_repo = document_repo
        self.operation_repo = operation_repo

    async def mark_queued(self, document_id: str, operation_id: str) -> None:
        await self.document_repo.update_status(document_id, status="uploaded", error_message=None)
        await self.operation_repo.update(
            operation_id,
            status="queued",
            stage="queued",
            message="Queued for processing",
            error_message=None,
        )

    async def mark_running(self, document_id: str, operation_id: str, *, stage: str, message: str) -> None:
        await self.document_repo.update_status(document_id, status="indexing", error_message=None)
        await self.operation_repo.update(
            operation_id,
            status="running",
            stage=stage,
            message=message,
            started_at=datetime.now(timezone.utc),
        )

    async def mark_waiting_remote(self, document_id: str, operation_id: str, *, message: str) -> None:
        await self.document_repo.update_status(document_id, status="indexing", error_message=None)
        await self.operation_repo.update(
            operation_id,
            status="running",
            stage="waiting_remote",
            message=message,
        )

    async def mark_succeeded(self, document_id: str, operation_id: str) -> None:
        await self.document_repo.update_status(document_id, status="ready", error_message=None)
        await self.operation_repo.update(
            operation_id,
            status="succeeded",
            stage="complete",
            message="Ready",
            finished_at=datetime.now(timezone.utc),
        )

    async def mark_failed(self, document_id: str, operation_id: str, *, error_message: str) -> None:
        await self.document_repo.update_status(document_id, status="failed", error_message=error_message)
        await self.operation_repo.update(
            operation_id,
            status="failed",
            stage="failed",
            message="Processing failed",
            error_message=error_message,
            finished_at=datetime.now(timezone.utc),
        )
