from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.services.file_storage import FileStorage
from app.services.job_service import JobService
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow


class DocumentService:
    def __init__(self, session: Session):
        self.session = session
        self.documents = DocumentRepository(session)
        self.storage = FileStorage()

    def upload(self, *, actor_id: str, file: UploadFile) -> tuple[DocumentRow, str]:
        path = self.storage.save_upload(file)
        document = self.documents.create(
            owner_id=actor_id,
            filename=file.filename or path.name,
            content_type=file.content_type or "application/octet-stream",
            storage_path=str(path),
            metadata={"original_filename": file.filename},
        )
        self.documents.audit(
            actor_id=actor_id,
            event="document.uploaded",
            target_id=document.id,
            metadata={"filename": document.filename},
        )
        job_id = JobService(self.session).enqueue_index_document(document_id=document.id)
        return document, job_id

    def get_ready_or_404(self, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document or document.status == "deleted":
            raise not_found("Document not found")
        return document

    def delete(self, *, actor_id: str, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        self.documents.mark_deleted(document)
        self.documents.audit(
            actor_id=actor_id,
            event="document.deleted",
            target_id=document.id,
            metadata={"filename": document.filename},
        )
        return document

