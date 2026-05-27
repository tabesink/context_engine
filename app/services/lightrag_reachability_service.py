from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse
import socket

import httpx

from app.core.config import Settings, get_settings
from app.services.lightrag_domain_registry import LightRAGDomainRegistry


@dataclass(frozen=True)
class LightRAGReachabilityReport:
    domain_id: str
    base_url: str
    healthy: bool
    code: str | None = None
    reason_code: str | None = None
    reason: str | None = None
    status_code: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.healthy,
            "code": self.code,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "status_code": self.status_code,
        }


class LightRAGReachabilityService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        http_get: Callable[..., httpx.Response] | None = None,
        dns_lookup: Callable[[str], object] | None = None,
    ):
        self.settings = settings or get_settings()
        self.http_get = http_get or httpx.get
        self.dns_lookup = dns_lookup or (lambda host: socket.getaddrinfo(host, None))

    def probe(self, domain_id: str | None) -> LightRAGReachabilityReport:
        domain = LightRAGDomainRegistry(settings=self.settings).get_required(domain_id)
        headers: dict[str, str] = {}
        if domain.api_key:
            headers["X-API-Key"] = domain.api_key

        dns_failure = self._dns_failure(domain.base_url)
        if dns_failure:
            return LightRAGReachabilityReport(
                domain_id=domain.id,
                base_url=domain.base_url,
                healthy=False,
                code="lightrag_domain_unreachable",
                reason_code="dns_failed",
                reason=dns_failure,
            )

        try:
            response = self.http_get(
                f"{domain.base_url}/health",
                headers=headers,
                timeout=self.settings.lightrag_timeout_seconds,
            )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            reason_code = self._network_reason_code(exc)
            return LightRAGReachabilityReport(
                domain_id=domain.id,
                base_url=domain.base_url,
                healthy=False,
                code="lightrag_domain_unreachable",
                reason_code=reason_code,
                reason=self._format_exception(exc),
            )
        except httpx.HTTPError as exc:
            return LightRAGReachabilityReport(
                domain_id=domain.id,
                base_url=domain.base_url,
                healthy=False,
                code="lightrag_domain_unreachable",
                reason_code="http_error",
                reason=self._format_exception(exc),
            )

        if response.status_code < 400:
            return LightRAGReachabilityReport(
                domain_id=domain.id,
                base_url=domain.base_url,
                healthy=True,
                status_code=response.status_code,
            )
        return LightRAGReachabilityReport(
            domain_id=domain.id,
            base_url=domain.base_url,
            healthy=False,
            code="lightrag_domain_unhealthy",
            reason_code="bad_response",
            reason=f"LightRAG health endpoint returned HTTP {response.status_code}.",
            status_code=response.status_code,
        )

    def _dns_failure(self, base_url: str) -> str | None:
        host = urlparse(base_url).hostname
        if not host or host in {"localhost", "127.0.0.1", "0.0.0.0"}:
            return None
        try:
            self.dns_lookup(host)
        except socket.gaierror as exc:
            return self._format_exception(exc)
        return None

    @staticmethod
    def _network_reason_code(exc: Exception) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return "timeout"
        text = str(exc).lower()
        if "name resolution" in text or "temporary failure" in text:
            return "dns_failed"
        if "connection refused" in text or "errno 111" in text:
            return "connection_refused"
        return "connect_error"

    @staticmethod
    def _format_exception(exc: Exception) -> str:
        message = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
        if message:
            return f"{exc.__class__.__name__}: {message}"
        return exc.__class__.__name__
