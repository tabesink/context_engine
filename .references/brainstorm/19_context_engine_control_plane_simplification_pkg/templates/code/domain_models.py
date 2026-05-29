"""Target LightRAG domain domain-model sketch.

Adapt this into app/domain/models.py or the current LightRAG domain model module.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class LightRAGDomainState(str, Enum):
    CREATING = "creating"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    DELETED = "deleted"


class LightRAGDomainHealth(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class LightRAGDomain(BaseModel):
    id: str
    display_name: str
    state: LightRAGDomainState
    health_status: LightRAGDomainHealth = LightRAGDomainHealth.UNKNOWN
    base_url: str | None = None
    container_name: str | None = None
    host_port: int | None = None
    embedding_profile_id: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_by_user_id: str | None = None
    created_at: datetime
    updated_at: datetime
