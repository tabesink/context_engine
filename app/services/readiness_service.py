from dataclasses import dataclass

import httpx
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.lightrag_domain_registry import LightRAGDomainRegistry


@dataclass(frozen=True)
class ReadinessReport:
    status: str
    services: dict[str, str]


class ReadinessService:
    def __init__(self, *, settings: Settings):
        self.settings = settings

    def check(self, *, session: Session) -> ReadinessReport:
        services = {
            "database": "healthy",
            "redis": "healthy",
            "lightrag": "unhealthy",
            "domain_registry": "unhealthy",
        }

        if not self._is_database_healthy(session):
            services["database"] = "unhealthy"

        if not self.settings.index_jobs_inline and not self._is_redis_healthy():
            services["redis"] = "unhealthy"

        default_domain = self._default_domain()
        if default_domain is not None:
            services["domain_registry"] = "healthy"
            if self._is_lightrag_healthy(default_domain):
                services["lightrag"] = "healthy"

        status = "ready" if all(value == "healthy" for value in services.values()) else "not_ready"
        return ReadinessReport(status=status, services=services)

    def _is_database_healthy(self, session: Session) -> bool:
        try:
            session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def _is_redis_healthy(self) -> bool:
        try:
            redis.Redis.from_url(self.settings.redis_url).ping()
            return True
        except Exception:
            return False

    def _default_domain(self):
        try:
            return LightRAGDomainRegistry(settings=self.settings).get_default()
        except Exception:
            return None

    def _is_lightrag_healthy(self, default_domain) -> bool:
        headers: dict[str, str] = {}
        if default_domain.api_key:
            headers["X-API-Key"] = default_domain.api_key
        try:
            response = httpx.get(
                f"{default_domain.base_url}/health",
                headers=headers,
                timeout=self.settings.lightrag_timeout_seconds,
            )
            return response.status_code < 400
        except Exception:
            return False
