from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LightRAGDomainCreateRequest(BaseModel):
    domain_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")
    display_name: str | None = None
    host_port: int | None = Field(default=None, ge=1, le=65535)
    make_default: bool = False


class LightRAGDomain(BaseModel):
    id: str
    display_name: str
    workspace: str | None = None
    postgres_database: str | None = None
    postgres_user: str | None = None
    host: str = "127.0.0.1"
    host_port: int = Field(ge=1, le=65535)
    container_port: int = Field(default=9621, ge=1, le=65535)
    base_url: str
    host_base_url: str
    container_base_url: str
    container_name: str
    service_name: str
    status: str = "configured"
    paths: dict[str, str]
    is_default: bool = False
    is_healthy: bool | None = None
    created_at: datetime
    updated_at: datetime

    def to_manifest_dict(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        data["created_at"] = _datetime_to_z(self.created_at)
        data["updated_at"] = _datetime_to_z(self.updated_at)
        return data


class LightRAGDomainOperationResult(BaseModel):
    id: str
    operation: str
    status: str
    service_name: str
    message: str | None = None


class LightRAGDomainRemoveResponse(BaseModel):
    id: str
    archived: bool
    archive_path: str | None = None
    permanent: bool = False


def _datetime_to_z(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
