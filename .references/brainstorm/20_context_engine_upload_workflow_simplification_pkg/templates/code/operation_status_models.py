"""Upload workflow operation status model sketch.

Adapt into app/domain/models.py or the existing operation/job model module.
"""

from enum import Enum
from pydantic import BaseModel


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class OperationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class OperationStage(str, Enum):
    QUEUED = "queued"
    SAVING = "saving"
    PARSING = "parsing"
    EXTRACTING_ASSETS = "extracting_assets"
    INDEXING_LIGHTRAG = "indexing_lightrag"
    WAITING_REMOTE = "waiting_remote"
    COMPLETE = "complete"
    FAILED = "failed"


class OperationResourceType(str, Enum):
    DOCUMENT = "document"
    DOMAIN = "domain"
    PROVIDER = "provider"
    SYSTEM = "system"


class UploadOperationSummary(BaseModel):
    id: str
    type: str = "document_ingest"
    status: OperationStatus
    stage: OperationStage | None = None
    message: str | None = None
