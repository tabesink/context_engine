"""LightRAG domain screen builders."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def build_lightrag_domains_screen(payload: dict[str, Any]) -> ScreenResult:
    domains = payload.get("domains") if isinstance(payload, dict) else []
    rows = [
        {
            "#": index,
            "domain": domain.get("id", ""),
            "display": domain.get("display_name", ""),
            "port": domain.get("host_port", ""),
            "status": domain.get("status", ""),
            "default": "yes" if domain.get("is_default") else "no",
        }
        for index, domain in enumerate(domains or [], start=1)
        if isinstance(domain, dict)
    ]
    return ScreenResult(
        title="LightRAG Domains",
        api_group="lightrag_domains",
        sections=[
            ScreenSection(
                title="Configured Domains",
                rows=rows,
                columns=["#", "domain", "display", "port", "status", "default"],
                text=None if rows else "No LightRAG domains configured.",
            )
        ],
        actions=[
            ScreenAction("Create domain", "POST /admin/lightrag/domains"),
            ScreenAction("Show domain detail", "GET /admin/lightrag/domains/{domain_id}"),
            ScreenAction("Start domain", "POST /admin/lightrag/domains/{domain_id}/up"),
            ScreenAction("Stop domain", "POST /admin/lightrag/domains/{domain_id}/down"),
            ScreenAction("Recreate domain", "POST /admin/lightrag/domains/{domain_id}/recreate"),
            ScreenAction("Regenerate domain files", "POST /admin/lightrag/domains/{domain_id}/regenerate"),
            ScreenAction("Archive remove domain", "DELETE /admin/lightrag/domains/{domain_id}"),
            ScreenAction("Permanent delete domain", "DELETE /admin/lightrag/domains/{domain_id}?permanent=true"),
        ],
        raw=payload,
    )
