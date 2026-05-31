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
    operation_type: str
    status: OperationStatus
    resource_type: str | None = None
    resource_id: str | None = None
    requested_by_user_id: str | None = None
    stage: str | None = None
    message: str | None = None
    progress_current: int | None = None
    progress_total: int | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime

