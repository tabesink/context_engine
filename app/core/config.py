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
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "admin-password"
    lightrag_enabled: bool = False
    lightrag_base_url: str = "http://localhost:9621"
    lightrag_api_key: str | None = None
    lightrag_domain: str = "default"
    lightrag_domain_manifest: Path | None = None
    lightrag_timeout_seconds: float = 10.0

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

