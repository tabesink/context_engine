import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class LightRAGDomain:
    name: str
    base_url: str
    api_key: str | None = None


def resolve_lightrag_domain(
    *,
    settings: Settings | None = None,
    domain: str | None = None,
    manifest_path: Path | None = None,
) -> LightRAGDomain:
    settings = settings or get_settings()
    requested = domain or settings.lightrag_domain
    path = manifest_path if manifest_path is not None else settings.lightrag_domain_manifest

    if path and path.is_file():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        entry = _domain_entry(manifest, requested)
        if entry:
            return LightRAGDomain(
                name=requested,
                base_url=str(entry.get("base_url") or settings.lightrag_base_url).rstrip("/"),
                api_key=entry.get("api_key") or settings.lightrag_api_key,
            )

    return LightRAGDomain(
        name=requested,
        base_url=settings.lightrag_base_url.rstrip("/"),
        api_key=settings.lightrag_api_key,
    )


def _domain_entry(manifest: dict[str, Any], requested: str) -> dict[str, Any] | None:
    domains = manifest.get("domains", manifest)
    if isinstance(domains, dict):
        entry = domains.get(requested)
        return entry if isinstance(entry, dict) else None
    if isinstance(domains, list):
        for entry in domains:
            if isinstance(entry, dict) and (
                entry.get("id") == requested or entry.get("name") == requested
            ):
                return entry
    return None
