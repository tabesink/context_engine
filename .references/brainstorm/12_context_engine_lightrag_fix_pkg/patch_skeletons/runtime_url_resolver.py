"""
Patch skeleton for app/services/lightrag_domain_registry.py

Goal:
- Do not trust persisted base_url as canonical.
- Compute runtime URL from host_base_url/container_base_url and execution mode.
"""

from typing import Any


def _runtime_base_url(entry: dict[str, Any], *, docker_execution_mode: str) -> str:
    """Return the correct LightRAG URL for the current runtime.

    Rules:
    - Docker/socket mode: API/worker are inside Docker network, so use container_base_url.
    - Host/local mode: caller is outside Docker network, so use host_base_url.
    - Legacy manifests may only have base_url; use it as a fallback.
    - Raise a registry invalid error if no usable URL exists.
    """

    mode = (docker_execution_mode or "").strip().lower()

    host_base_url = _optional_url(entry.get("host_base_url"))
    container_base_url = _optional_url(entry.get("container_base_url"))
    legacy_base_url = _optional_url(entry.get("base_url"))

    if mode == "socket":
        if container_base_url:
            return container_base_url
        if legacy_base_url:
            # Optional: log warning that legacy base_url is being used.
            return legacy_base_url
        if host_base_url:
            # Fallback only. In Docker this may not work.
            # Optional: log warning.
            return host_base_url

    else:
        if host_base_url:
            return host_base_url
        if legacy_base_url:
            # Optional: log warning that legacy base_url is being used.
            return legacy_base_url
        if container_base_url:
            # Fallback only. From host this may not work.
            # Optional: log warning.
            return container_base_url

    raise LightRAGDomainRegistryInvalidError(
        f"LightRAG domain '{entry.get('id') or entry.get('name')}' does not define a usable runtime URL"
    )


# Existing helper likely already exists in registry file.
def _optional_url(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text.rstrip("/") if text else None


class LightRAGDomainRegistryInvalidError(Exception):
    pass
