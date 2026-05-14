from datetime import datetime

from pydantic import BaseModel

from app.domain.models import DocumentStatus


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict = {}
    error_message: str | None = None


class UploadResponse(BaseModel):
    document: DocumentResponse
    job_id: str | None = None


class PageResponse(BaseModel):
    document_id: str
    page_number: int
    text: str
    metadata: dict = {}


class StructureResponse(BaseModel):
    document_id: str
    tree: list[dict]

