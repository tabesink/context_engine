from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import httpx
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.lightrag_domain_registry import LightRAGDomainRegistry, LightRAGDomainRuntime


@dataclass(frozen=True)
class ReadinessReport:
    status: str
    services: dict[str, str]
    details: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ServiceReadinessDetail:
    status: str
    reason: str | None
    latency_ms: int
    checked_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "latency_ms": self.latency_ms,
            "checked_at": self.checked_at,
        }


class ReadinessService:
    _SERVICE_ORDER = ("database", "redis", "lightrag", "domain_registry")

    def __init__(self, *, settings: Settings):
        self.settings = settings

    def check(self, *, session: Session) -> ReadinessReport:
        database = self._probe_database(session)
        redis_status = self._probe_redis()
        domain_registry, default_domain = self._probe_domain_registry()
        lightrag = self._probe_lightrag(default_domain)

        detail_map = {
            "database": database,
            "redis": redis_status,
            "lightrag": lightrag,
            "domain_registry": domain_registry,
        }
        services = {service: detail_map[service].status for service in self._SERVICE_ORDER}
        details = {service: detail_map[service].as_dict() for service in self._SERVICE_ORDER}
        status = "ready" if all(value == "healthy" for value in services.values()) else "not_ready"
        return ReadinessReport(status=status, services=services, details=details)

    def _probe_database(self, session: Session) -> ServiceReadinessDetail:
        started_at = perf_counter()
        checked_at = self._checked_at()
        try:
            session.execute(text("SELECT 1"))
            return self._healthy_detail(started_at=started_at, checked_at=checked_at)
        except Exception as exc:
            return self._unhealthy_detail(
                started_at=started_at,
                checked_at=checked_at,
                reason=self._format_reason("Database query failed", exc),
            )

    def _probe_redis(self) -> ServiceReadinessDetail:
        started_at = perf_counter()
        checked_at = self._checked_at()
        if self.settings.index_jobs_inline:
            return self._healthy_detail(
                started_at=started_at,
                checked_at=checked_at,
                reason="Redis check skipped because inline jobs are enabled.",
            )
        try:
            redis.Redis.from_url(self.settings.redis_url).ping()
            return self._healthy_detail(started_at=started_at, checked_at=checked_at)
        except Exception as exc:
            return self._unhealthy_detail(
                started_at=started_at,
                checked_at=checked_at,
                reason=self._format_reason("Redis ping failed", exc),
            )

    def _probe_domain_registry(self) -> tuple[ServiceReadinessDetail, LightRAGDomainRuntime | None]:
        started_at = perf_counter()
        checked_at = self._checked_at()
        try:
            default_domain = LightRAGDomainRegistry(settings=self.settings).get_default()
            detail = self._healthy_detail(started_at=started_at, checked_at=checked_at)
            return detail, default_domain
        except Exception as exc:
            detail = self._unhealthy_detail(
                started_at=started_at,
                checked_at=checked_at,
                reason=self._format_reason("Domain registry is unavailable", exc),
            )
            return detail, None

    def _probe_lightrag(self, default_domain: LightRAGDomainRuntime | None) -> ServiceReadinessDetail:
        started_at = perf_counter()
        checked_at = self._checked_at()
        if default_domain is None:
            return self._unhealthy_detail(
                started_at=started_at,
                checked_at=checked_at,
                reason="Default LightRAG domain is unavailable.",
            )

        headers: dict[str, str] = {}
        if default_domain.api_key:
            headers["X-API-Key"] = default_domain.api_key
        try:
            response = httpx.get(
                f"{default_domain.base_url}/health",
                headers=headers,
                timeout=self.settings.lightrag_timeout_seconds,
            )
            if response.status_code < 400:
                return self._healthy_detail(started_at=started_at, checked_at=checked_at)
            return self._unhealthy_detail(
                started_at=started_at,
                checked_at=checked_at,
                reason=f"LightRAG health endpoint returned HTTP {response.status_code}.",
            )
        except Exception as exc:
            return self._unhealthy_detail(
                started_at=started_at,
                checked_at=checked_at,
                reason=self._format_reason("LightRAG health check failed", exc),
            )

    def _healthy_detail(
        self,
        *,
        started_at: float,
        checked_at: str,
        reason: str | None = None,
    ) -> ServiceReadinessDetail:
        return ServiceReadinessDetail(
            status="healthy",
            reason=reason,
            latency_ms=self._latency_ms(started_at),
            checked_at=checked_at,
        )

    def _unhealthy_detail(
        self,
        *,
        started_at: float,
        checked_at: str,
        reason: str,
    ) -> ServiceReadinessDetail:
        return ServiceReadinessDetail(
            status="unhealthy",
            reason=reason,
            latency_ms=self._latency_ms(started_at),
            checked_at=checked_at,
        )

    def _checked_at(self) -> str:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def _latency_ms(self, started_at: float) -> int:
        return int((perf_counter() - started_at) * 1000)

    def _format_reason(self, prefix: str, exc: Exception) -> str:
        message = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
        exc_name = exc.__class__.__name__
        reason = f"{prefix}: {exc_name}"
        if message:
            reason = f"{reason} ({message})"
        return reason[:220]
