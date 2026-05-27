from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.services.lightrag_domain_registry import LightRAGDomainRegistry


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
    registry = LightRAGDomainRegistry(
        settings=settings,
        registry_path=manifest_path or settings.lightrag_domain_registry,
    )
    resolved = registry.validate_available(domain)
    base_url = resolved.base_url
    docker_execution_mode = settings.lightrag_docker_execution_mode.strip().lower()
    if docker_execution_mode == "socket" and resolved.container_base_url:
        base_url = resolved.container_base_url
    elif docker_execution_mode == "host" and resolved.host_base_url:
        base_url = resolved.host_base_url
    return LightRAGDomain(
        name=resolved.id,
        base_url=base_url,
        api_key=resolved.api_key,
    )
