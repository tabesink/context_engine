"""Target operation domain model sketch.

Adapt this into app/domain/models.py or the existing domain-model module.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class OperationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class OperationResourceType(str, Enum):
    DOCUMENT = "document"
    DOMAIN = "domain"
    PROVIDER = "provider"
    SYSTEM = "system"


class OperationType(str, Enum):
    DOCUMENT_INGEST = "document_ingest"
    DOCUMENT_REINDEX = "document_reindex"
    DOMAIN_CREATE = "domain_create"
    DOMAIN_START = "domain_start"
    DOMAIN_STOP = "domain_stop"
    DOMAIN_DELETE = "domain_delete"
    PROVIDER_TEST = "provider_test"


class Operation(BaseModel):
    id: str
    operation_type: str = Field(alias="kind")  # keep alias during jobs compatibility phase if needed
    status: OperationStatus
    resource_type: OperationResourceType
    resource_id: str | None = None
    requested_by_user_id: str | None = None
    progress_current: int | None = None
    progress_total: int | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


# Temporary compatibility alias. Remove after old job vocabulary is gone.
JobStatus = OperationStatus
