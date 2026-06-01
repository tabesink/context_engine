from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import JobStatus, OperationStatus


class JobResponse(BaseModel):
    id: str
    kind: str
    status: JobStatus
    document_id: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class OperationResponse(BaseModel):
    id: str
    type: str
    status: OperationStatus
    stage: str | None = None
    progress: int | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    resource_label: str | None = None
    actor_user_id: str | None = None
    message: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime

