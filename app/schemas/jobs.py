from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import JobStatus


class JobResponse(BaseModel):
    id: str
    kind: str
    status: JobStatus
    document_id: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

