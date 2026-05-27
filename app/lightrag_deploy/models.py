from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DomainRetrievalDefaults(BaseModel):
    top_k: int = Field(default=10, ge=1)
    chunk_top_k: int = Field(default=10, ge=1)
    chunk_rerank_top_k: int = Field(default=10, ge=1)
    max_token_for_text_unit: int = Field(default=4000, ge=1)
    max_token_for_global_context: int = Field(default=4000, ge=1)
    max_token_for_local_context: int = Field(default=4000, ge=1)


class LightRAGDomainCreateRequest(BaseModel):
    domain_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")
    display_name: str | None = None
    host_port: int | None = Field(default=None, ge=1, le=65535)
    embedding_profile_id: str | None = None
    make_default: bool = False
    top_k: int = Field(default=10, ge=1)
    chunk_top_k: int = Field(default=10, ge=1)
    chunk_rerank_top_k: int = Field(default=10, ge=1)
    max_token_for_text_unit: int = Field(default=4000, ge=1)
    max_token_for_global_context: int = Field(default=4000, ge=1)
    max_token_for_local_context: int = Field(default=4000, ge=1)


class DomainEmbeddingSnapshot(BaseModel):
    profile_id: str
    provider: str
    binding: str
    base_url: str
    api_key_env_var: str | None = None
    model: str
    dimensions: int | None = None
    token_limit: int | None = None
    send_dimensions: bool = False
    use_base64: bool = True
    fingerprint: str


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
    embedding: DomainEmbeddingSnapshot | None = None
    embedding_locked_at: datetime | None = None
    embedding_lock_reason: str | None = None
    first_ingested_document_id: str | None = None
    retrieval_defaults: DomainRetrievalDefaults = Field(default_factory=DomainRetrievalDefaults)
    is_default: bool = False
    is_healthy: bool | None = None
    created_at: datetime
    updated_at: datetime

    def to_manifest_dict(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        data["created_at"] = _datetime_to_z(self.created_at)
        data["updated_at"] = _datetime_to_z(self.updated_at)
        if self.embedding_locked_at is not None:
            data["embedding_locked_at"] = _datetime_to_z(self.embedding_locked_at)
        return data


class LightRAGDomainOperationResult(BaseModel):
    id: str
    operation: str
    status: str
    service_name: str
    message: str | None = None


class LightRAGDomainRepairResult(BaseModel):
    id: str
    domain_id: str
    operation: str = "repair"
    status: str
    service_name: str
    storage_backend: str
    postgres_database: str | None = None
    postgres_user: str | None = None
    postgres_role_exists: bool | None = None
    postgres_database_exists: bool | None = None
    extensions: dict[str, dict[str, str | None]] = Field(default_factory=dict)
    host_base_url: str
    container_base_url: str
    runtime_base_url: str
    docker_operation: str
    health: dict[str, Any] | None = None
    is_healthy: bool | None = None
    message: str | None = None


class LightRAGDomainRemoveResponse(BaseModel):
    id: str
    archived: bool
    archive_path: str | None = None
    permanent: bool = False


class LightRAGDomainPurgePreview(BaseModel):
    domain_id: str
    documents: int
    original_uploads: int
    assets: int
    chunks: int
    pages: int
    sections: int
    blocks: int
    estimated_bytes: int
    will_delete: list[str]


class LightRAGDomainPurgeResult(BaseModel):
    domain_id: str
    state: str
    purged_documents: int
    purged_original_uploads: int
    purged_artifact_roots: int
    purged_processing_rows: dict[str, int]
    canceled_jobs: int
    cleared_job_document_references: int
    deleted_domain_root: bool
    deleted_domain_archive: bool


def _datetime_to_z(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
