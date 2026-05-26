from functools import lru_cache
import json
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Context Engine"
    environment: str = "local"
    api_host: str = "127.0.0.1"
    client_host: str = "127.0.0.1"
    lightrag_host: str = "127.0.0.1"
    secret_key: str = "dev-secret-change-me"
    access_token_minutes: int = 60
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    index_jobs_inline: bool = False
    lightrag_status_poll_interval_seconds: float = 10.0
    storage_root: Path = Path(".data/uploads")
    allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    seed_admin_username: str = "admin"
    seed_admin_password: str = "admin-password"
    # Semantic retrieval is remote-LightRAG-only in this service.
    lightrag_domain_registry: Path = Field(
        default=Path(".data/lightrag/domains.json"),
    )
    lightrag_timeout_seconds: float = 10.0
    query_log_store_text: bool = False
    query_log_retention_days: int = 30
    lightrag_deploy_enabled: bool = False
    lightrag_deploy_root: Path = Path(".data/lightrag")
    lightrag_domains_root: Path = Path(".data/lightrag/domains")
    lightrag_compose_file: Path = Path(".data/lightrag/docker-compose.lightrag-domains.yml")
    lightrag_deleted_root: Path = Path(".data/lightrag/deleted")
    lightrag_default_port_start: int = 9621
    lightrag_default_container_port: int = 9621
    lightrag_docker_network: str = "context_engine_lightrag"
    lightrag_domain_env_filename: str = "domain.env"
    lightrag_dockerfile: Path = Path("docker/lightrag.Dockerfile")
    lightrag_build_context: Path = Path(".")
    lightrag_postgres_url: str | None = None
    lightrag_postgres_host: str = "postgres"
    lightrag_postgres_port: int = 5432
    lightrag_postgres_database_prefix: str = "lightrag"
    lightrag_postgres_user_prefix: str = "lightrag"
    lightrag_postgres_password: str = "lightrag"
    lightrag_redis_url: str | None = None
    lightrag_neo4j_uri: str | None = None
    lightrag_neo4j_username: str | None = None
    lightrag_neo4j_password: str | None = None
    lightrag_llm_binding: str = "openai"
    lightrag_llm_binding_host: str | None = None
    lightrag_llm_binding_api_key: str | None = None
    lightrag_llm_model: str | None = None
    lightrag_keyword_llm_model: str | None = None
    lightrag_query_llm_model: str | None = None
    lightrag_vlm_llm_model: str | None = None
    lightrag_embedding_binding: str = "openai"
    lightrag_embedding_binding_host: str | None = None
    lightrag_embedding_binding_api_key: str | None = None
    lightrag_embedding_model: str | None = None
    lightrag_embedding_dim: int | None = None
    lightrag_embedding_token_limit: int | None = None
    lightrag_embedding_send_dim: bool | None = None
    lightrag_embedding_use_base64: bool | None = None
    lightrag_openai_llm_max_tokens: int | None = None
    lightrag_openai_llm_max_completion_tokens: int | None = None
    lightrag_openai_llm_temperature: float | None = None
    lightrag_openai_llm_extra_body: str | None = None
    openai_api_key: str | None = None
    aws_bearer_token_bedrock: str | None = None
    ollama_base_url: str = "http://host.docker.internal:11434/v1"
    default_openai_base_url: str = "https://api.openai.com/v1"
    default_bedrock_openai_base_url: str | None = None
    ai_secret_encryption_key: str | None = None
    lightrag_archive_deleted_domains: bool = True
    lightrag_allow_permanent_delete: bool = False
    lightrag_docker_execution_mode: str = "host"
    lightrag_docker_compose_bin: str = "docker compose"
    lightrag_docker_timeout_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if isinstance(value, list):
            return value
        if not isinstance(value, str):
            return value

        raw = value.strip()
        if not raw:
            return ["*"]
        if raw == "*":
            return ["*"]

        if raw.startswith("["):
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]

        return [item.strip() for item in raw.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_runtime_settings(self) -> "Settings":
        env = self.environment.strip().lower()
        database_url = self.database_url.strip()
        if not database_url:
            raise ValueError("DATABASE_URL must be configured.")
        if database_url.startswith("sqlite") and env != "test":
            raise ValueError("SQLite is only allowed when ENVIRONMENT=test. Use PostgreSQL.")
        if env != "test" and not database_url.startswith("postgresql"):
            raise ValueError("PostgreSQL is the only supported runtime database.")

        if env in {"production", "staging"}:
            weak_secret_keys = {
                "dev-secret-change-me",
                "change-me",
                "change-me-in-production",
            }
            if self.secret_key in weak_secret_keys:
                raise ValueError("SECRET_KEY must be set to a strong production/staging value.")
            if self.allowed_origins == ["*"]:
                raise ValueError("ALLOWED_ORIGINS cannot be '*' in production/staging.")
            weak_seed_passwords = {"admin", "admin123", "admin-password", "change-me"}
            if self.seed_admin_password in weak_seed_passwords:
                raise ValueError("SEED_ADMIN_PASSWORD is too weak for production/staging.")

        if not self.lightrag_domain_registry:
            raise ValueError("LIGHTRAG_DOMAIN_REGISTRY must be configured.")
        if self.lightrag_deploy_enabled:
            if not self.lightrag_dockerfile:
                raise ValueError("LIGHTRAG_DOCKERFILE must be configured when deploy is enabled.")
            if not self.lightrag_build_context:
                raise ValueError("LIGHTRAG_BUILD_CONTEXT must be configured when deploy is enabled.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

