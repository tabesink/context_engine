"""
Suggested new file:
app/services/lightrag_domain_health.py
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
import socket

import httpx

from app.services.lightrag_domain_registry import LightRAGDomainRegistry


@dataclass(frozen=True)
class LightRAGDomainHealth:
    domain_id: str
    base_url: str
    ok: bool
    reason: str | None = None
    detail: str | None = None
    status_code: int | None = None


class LightRAGDomainHealthProbe:
    def __init__(
        self,
        *,
        registry: LightRAGDomainRegistry | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.registry = registry or LightRAGDomainRegistry()
        self.timeout_seconds = timeout_seconds

    def check(self, domain_id: str) -> LightRAGDomainHealth:
        domain = self.registry.get_required(domain_id)
        base_url = domain.base_url.rstrip("/")

        dns_result = self._check_dns(base_url)
        if dns_result is not None:
            return LightRAGDomainHealth(
                domain_id=domain.id,
                base_url=base_url,
                ok=False,
                reason="dns_failed",
                detail=dns_result,
            )

        # Prefer known health endpoint if LightRAG exposes one in this deployment.
        # Keep fallback to root because LightRAG versions may differ.
        for path in ("/health", "/healthz", "/"):
            url = f"{base_url}{path}"
            try:
                response = httpx.get(url, timeout=self.timeout_seconds)
            except httpx.TimeoutException as exc:
                return LightRAGDomainHealth(
                    domain_id=domain.id,
                    base_url=base_url,
                    ok=False,
                    reason="timeout",
                    detail=str(exc),
                )
            except httpx.ConnectError as exc:
                return LightRAGDomainHealth(
                    domain_id=domain.id,
                    base_url=base_url,
                    ok=False,
                    reason="connect_error",
                    detail=str(exc),
                )
            except httpx.HTTPError as exc:
                return LightRAGDomainHealth(
                    domain_id=domain.id,
                    base_url=base_url,
                    ok=False,
                    reason="http_error",
                    detail=str(exc),
                )

            # Treat any non-5xx HTTP response as proof that the service is reachable.
            # Tighten this once a stable LightRAG health endpoint is confirmed.
            if response.status_code < 500:
                return LightRAGDomainHealth(
                    domain_id=domain.id,
                    base_url=base_url,
                    ok=True,
                    status_code=response.status_code,
                )

        return LightRAGDomainHealth(
            domain_id=domain.id,
            base_url=base_url,
            ok=False,
            reason="bad_response",
            detail="LightRAG returned only 5xx responses to probe endpoints.",
        )

    def _check_dns(self, base_url: str) -> str | None:
        parsed = urlparse(base_url)
        host = parsed.hostname
        if not host:
            return "Runtime URL does not include a hostname."

        if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
            return None

        try:
            socket.getaddrinfo(host, None)
            return None
        except socket.gaierror as exc:
            return str(exc)
