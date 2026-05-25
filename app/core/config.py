from functools import lru_cache
import json
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Context Engine"
    environment: str = "local"
    secret_key: str = "dev-secret-change-me"
    access_token_minutes: int = 60
    database_url: str = "sqlite:///./.data/context_engine.db"
    redis_url: str = "redis://localhost:6379/0"
    index_jobs_inline: bool = False
    storage_root: Path = Path(".data/uploads")
    allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    seed_admin_username: str = "admin"
    seed_admin_password: str = "admin-password"
    lightrag_enabled: bool = False
    lightrag_base_url: str = "http://localhost:9621"
    lightrag_api_key: str | None = None
    lightrag_domain: str = "default"
    lightrag_domain_manifest: Path | None = Path(".data/lightrag/domains.json")
    lightrag_timeout_seconds: float = 10.0
    lightrag_deploy_enabled: bool = False
    lightrag_deploy_root: Path = Path(".data/lightrag")
    lightrag_domains_root: Path = Path(".data/lightrag/domains")
    lightrag_domains_manifest: Path = Path(".data/lightrag/domains.json")
    lightrag_compose_file: Path = Path(".data/lightrag/docker-compose.lightrag-domains.yml")
    lightrag_deleted_root: Path = Path(".data/lightrag/deleted")
    lightrag_default_port_start: int = 9621
    lightrag_default_container_port: int = 9621
    lightrag_docker_network: str = "context_engine_lightrag"
    lightrag_domain_env_filename: str = "domain.env"
    lightrag_image: str = "ghcr.io/hkuds/lightrag:latest"
    lightrag_dockerfile: Path | None = None
    lightrag_build_context: Path | None = None
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
    lightrag_archive_deleted_domains: bool = True
    lightrag_allow_permanent_delete: bool = False
    lightrag_docker_execution_mode: str = "host"
    lightrag_docker_compose_bin: str = "docker compose"
    lightrag_docker_timeout_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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


@lru_cache
def get_settings() -> Settings:
    return Settings()

