from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Context Engine"
    environment: str = "local"
    secret_key: str = "dev-secret-change-me"
    access_token_minutes: int = 60
    database_url: str = "sqlite:///./.data/context_engine.db"
    redis_url: str = "redis://localhost:6379/0"
    index_jobs_inline: bool = False
    storage_root: Path = Path(".data/uploads")
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "admin-password"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

