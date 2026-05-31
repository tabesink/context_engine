"""Document upload service target contract.

Do not paste blindly. Adapt to the current repo's async/session conventions.
"""

from dataclasses import dataclass


@dataclass
class UploadResult:
    document_id: str
    operation_id: str
    status_url: str


class DocumentUploadService:
    def __init__(self, document_repo, operation_repo, status_service, storage_service, domain_service):
        self.document_repo = document_repo
        self.operation_repo = operation_repo
        self.status_service = status_service
        self.storage_service = storage_service
        self.domain_service = domain_service

    async def upload(self, *, file, domain_id: str, owner_id: str) -> UploadResult:
        # 1. Validate domain exists/running/usable.
        # 2. Store uploaded file.
        # 3. Create document with status=uploaded.
        # 4. Create operation: document_ingest, resource_type=document, resource_id=document.id.
        # 5. Mark queued through status service.
        # 6. Enqueue worker.
        # 7. Return document_id, operation_id, status_url.
        raise NotImplementedError
