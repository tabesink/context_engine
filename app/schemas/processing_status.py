from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ProcessingState = Literal[
    "idle",
    "queued",
    "busy",
    "partial_failure",
    "failed",
    "unreachable",
    "unknown",
]

DocumentProcessingState = Literal[
    "uploaded",
    "queued",
    "indexing",
    "ready",
    "failed",
    "deleted",
    "unknown",
]


class ProcessingCounts(BaseModel):
    queued: int = 0
    indexing: int = 0
    ready: int = 0
    failed: int = 0
    deleted: int = 0
    unknown: int = 0


class ActiveProcessingOperation(BaseModel):
    label: str | None = None
    current: int | None = None
    total: int | None = None
    message: str | None = None
    started_at: datetime | None = None


class ProcessingStatusError(BaseModel):
    code: str
    message: str
    source: Literal["context_engine", "lightrag"] = "context_engine"


class DocumentProcessingStatusItem(BaseModel):
    document_id: str
    filename: str
    status: DocumentProcessingState
    domain_id: str | None = None
    job_id: str | None = None
    job_status: str | None = None
    lightrag_status: str | None = None
    message: str | None = None
    can_retry: bool = False
    updated_at: datetime


class LightRAGPipelineStatus(BaseModel):
    reachable: bool
    pipeline_busy: bool = False
    job_name: str | None = None
    job_start: datetime | None = None
    latest_message: str | None = None
    history_tail: list[str] = Field(default_factory=list)
    update_status: dict = Field(default_factory=dict)


class DomainProcessingStatusResponse(BaseModel):
    domain_id: str
    state: ProcessingState
    is_busy: bool
    is_stale: bool = False
    updated_at: datetime
    counts: ProcessingCounts
    active: ActiveProcessingOperation | None = None
    documents: list[DocumentProcessingStatusItem] = Field(default_factory=list)
    lightrag: LightRAGPipelineStatus | None = None
    errors: list[ProcessingStatusError] = Field(default_factory=list)


class DocumentProcessingStatusResponse(BaseModel):
    document: DocumentProcessingStatusItem
    domain: DomainProcessingStatusResponse | None = None


class ProcessingStatusPagination(BaseModel):
    limit: int
    offset: int
    returned: int
    total: int


class ProcessingStatusListResponse(BaseModel):
    domain_id: str
    documents: list[DocumentProcessingStatusItem] = Field(default_factory=list)
    status_counts: ProcessingCounts = Field(default_factory=ProcessingCounts)
    pagination: ProcessingStatusPagination
    updated_at: datetime
