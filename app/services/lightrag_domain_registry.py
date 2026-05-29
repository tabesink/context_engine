import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.core.config import Settings, get_settings
from app.services.lightrag_domain_lifecycle_service import LightRAGDomainLifecycleService


UNAVAILABLE_STATUSES = {"stopped", "unhealthy", "archived", "error"}


class LightRAGDomainRegistryError(Exception):
    """Base class for domain registry errors."""


class LightRAGDomainIdRequiredError(LightRAGDomainRegistryError):
    pass


class LightRAGDomainNotFoundError(LightRAGDomainRegistryError):
    pass


class LightRAGDomainUnavailableError(LightRAGDomainRegistryError):
    pass


class LightRAGDomainRegistryInvalidError(LightRAGDomainRegistryError):
    pass


@dataclass(frozen=True)
class LightRAGDomainSummary:
    id: str
    display_name: str
    host_port: int | None
    is_default: bool
    is_healthy: bool | None
    status: str | None


@dataclass(frozen=True)
class LightRAGDomainRuntime:
    id: str
    display_name: str
    base_url: str
    host_base_url: str | None
    container_base_url: str | None
    api_key: str | None
    status: str | None
    is_healthy: bool | None
    is_default: bool


class LightRAGDomainRegistry:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        registry_path: Path | None = None,
        lifecycle: LightRAGDomainLifecycleService | None = None,
    ):
        self.settings = settings or get_settings()
        self.registry_path = registry_path or self.settings.lightrag_domain_registry
        self.lifecycle = lifecycle or LightRAGDomainLifecycleService()

    def list_domains(self) -> list[LightRAGDomainSummary]:
        blocked = self._blocked_domain_ids()
        domains: list[LightRAGDomainSummary] = []
        for domain in self._read_domain_entries():
            domain_id = str(domain["id"])
            if domain_id in blocked:
                continue
            domains.append(
                LightRAGDomainSummary(
                    id=domain_id,
                    display_name=str(domain.get("display_name") or domain_id),
                    host_port=_optional_int(domain.get("host_port")),
                    is_default=bool(domain.get("is_default", False)),
                    is_healthy=domain.get("is_healthy"),
                    status=_optional_string(domain.get("status")),
                )
            )
        return domains

    def get_required(self, domain_id: str | None) -> LightRAGDomainRuntime:
        requested = _require_domain_id(domain_id)
        entry = self._domain_entry(requested)
        if entry is None:
            raise LightRAGDomainNotFoundError(f"LightRAG domain '{requested}' does not exist")

        base_url = self._runtime_base_url(entry, requested)

        return LightRAGDomainRuntime(
            id=str(entry["id"]),
            display_name=str(entry.get("display_name") or entry["id"]),
            base_url=base_url,
            host_base_url=_optional_url(entry.get("host_base_url")),
            container_base_url=_optional_url(entry.get("container_base_url")),
            api_key=_optional_string(entry.get("api_key")),
            status=_optional_string(entry.get("status")),
            is_healthy=entry.get("is_healthy"),
            is_default=bool(entry.get("is_default", False)),
        )

    def get_default(self) -> LightRAGDomainRuntime:
        for entry in self._read_domain_entries():
            if entry.get("is_default") is True:
                return self.get_required(str(entry.get("id") or ""))
        raise LightRAGDomainNotFoundError("No default LightRAG domain is registered")

    def validate_available(self, domain_id: str | None) -> LightRAGDomainRuntime:
        domain = self.get_required(domain_id)
        try:
            is_active = self.lifecycle.is_active(domain.id)
        except OperationalError:
            # Test/local bootstrap environments may not have lifecycle tables yet.
            is_active = True
        if not is_active:
            raise LightRAGDomainUnavailableError(
                f"LightRAG domain '{domain.id}' is not available"
            )
        status = (domain.status or "").lower()
        if status in UNAVAILABLE_STATUSES:
            raise LightRAGDomainUnavailableError(
                f"LightRAG domain '{domain.id}' is not available"
            )
        return domain

    def _blocked_domain_ids(self) -> set[str]:
        try:
            return self.lifecycle.blocked_domain_ids()
        except OperationalError:
            return set()

    def _domain_entry(self, domain_id: str) -> dict[str, Any] | None:
        for entry in self._read_domain_entries():
            if entry.get("id") == domain_id:
                return entry
        return None

    def _runtime_base_url(self, entry: dict[str, Any], domain_id: str) -> str:
        mode = self.settings.lightrag_docker_execution_mode.strip().lower()
        host_base_url = _optional_url(entry.get("host_base_url"))
        container_base_url = _optional_url(entry.get("container_base_url"))

        if mode == "socket":
            if container_base_url:
                return container_base_url
        elif host_base_url:
            return host_base_url

        raise LightRAGDomainRegistryInvalidError(
            f"LightRAG domain '{domain_id}' does not define the required runtime URL for {mode!r} mode"
        )

    def _read_domain_entries(self) -> list[dict[str, Any]]:
        if not self.registry_path.is_file():
            return []
        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        domains = payload.get("domains", []) if isinstance(payload, dict) else []
        if isinstance(domains, list):
            return [entry for entry in domains if isinstance(entry, dict) and entry.get("id")]
        return []


def lightrag_domain_http_exception(exc: LightRAGDomainRegistryError) -> HTTPException:
    if isinstance(exc, LightRAGDomainNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


def _require_domain_id(domain_id: str | None) -> str:
    requested = (domain_id or "").strip()
    if not requested:
        raise LightRAGDomainIdRequiredError("lightrag_domain_id is required")
    return requested


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _optional_url(value: Any) -> str | None:
    text = _optional_string(value)
    if text is None:
        return None
    return text.rstrip("/")

