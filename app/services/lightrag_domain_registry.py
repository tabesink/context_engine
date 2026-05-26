import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.config import Settings, get_settings


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
    is_default: bool
    is_healthy: bool | None
    status: str | None


@dataclass(frozen=True)
class LightRAGDomainRuntime:
    id: str
    display_name: str
    base_url: str
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
    ):
        self.settings = settings or get_settings()
        self.registry_path = registry_path or self.settings.lightrag_domain_registry

    def list_domains(self) -> list[LightRAGDomainSummary]:
        return [
            LightRAGDomainSummary(
                id=domain["id"],
                display_name=str(domain.get("display_name") or domain["id"]),
                is_default=bool(domain.get("is_default", False)),
                is_healthy=domain.get("is_healthy"),
                status=_optional_string(domain.get("status")),
            )
            for domain in self._read_domain_entries()
        ]

    def get_required(self, domain_id: str | None) -> LightRAGDomainRuntime:
        requested = _require_domain_id(domain_id)
        entry = self._domain_entry(requested)
        if entry is None:
            raise LightRAGDomainNotFoundError(f"LightRAG domain '{requested}' does not exist")

        base_url = str(entry.get("base_url") or "").strip().rstrip("/")
        if not base_url:
            raise LightRAGDomainRegistryInvalidError(
                f"LightRAG domain '{requested}' does not define base_url"
            )

        return LightRAGDomainRuntime(
            id=str(entry.get("id") or requested),
            display_name=str(entry.get("display_name") or entry.get("name") or requested),
            base_url=base_url,
            api_key=_optional_string(entry.get("api_key")),
            status=_optional_string(entry.get("status")),
            is_healthy=entry.get("is_healthy"),
            is_default=bool(entry.get("is_default", False)),
        )

    def get_default(self) -> LightRAGDomainRuntime:
        for entry in self._read_domain_entries():
            if entry.get("is_default") is True:
                return self.get_required(str(entry.get("id") or entry.get("name") or ""))
        raise LightRAGDomainNotFoundError("No default LightRAG domain is registered")

    def validate_available(self, domain_id: str | None) -> LightRAGDomainRuntime:
        domain = self.get_required(domain_id)
        status = (domain.status or "").lower()
        if status in UNAVAILABLE_STATUSES:
            raise LightRAGDomainUnavailableError(
                f"LightRAG domain '{domain.id}' is not available"
            )
        return domain

    def _domain_entry(self, domain_id: str) -> dict[str, Any] | None:
        for entry in self._read_domain_entries():
            if entry.get("id") == domain_id or entry.get("name") == domain_id:
                return entry
        return None

    def _read_domain_entries(self) -> list[dict[str, Any]]:
        if not self.registry_path.is_file():
            return []
        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        domains = payload.get("domains", []) if isinstance(payload, dict) else []
        if isinstance(domains, dict):
            return [
                {"id": key, **value}
                for key, value in domains.items()
                if isinstance(key, str) and isinstance(value, dict)
            ]
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
