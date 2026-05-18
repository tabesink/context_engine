"""Inspect drawer rendering for backend API visibility."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from cli.renderers.tables import render_ascii_table
from cli.tui.renderers.json_view import render_json_view, safe_json


def render_inspect_view(
    console: Console,
    *,
    metadata: Any,
    fallback_method: str | None = None,
    fallback_route: str | None = None,
    request_payload: Any = None,
    response_payload: Any = None,
    selected_ids: dict[str, Any] | None = None,
) -> None:
    method = getattr(metadata, "method", None) or fallback_method or "unknown"
    route = getattr(metadata, "route", None) or fallback_route or "unknown"
    status_code = getattr(metadata, "status_code", None)
    elapsed_ms = getattr(metadata, "elapsed_ms", None)
    request_summary = getattr(metadata, "request_summary", None)
    response_summary = getattr(metadata, "response_summary", None)

    rows = [
        {"field": "Method", "value": method},
        {"field": "Route", "value": route},
        {"field": "Status", "value": status_code if status_code is not None else "unknown"},
        {"field": "Latency", "value": f"{elapsed_ms} ms" if elapsed_ms is not None else "unknown"},
    ]
    render_ascii_table("", rows, ["field", "value"], console=console)

    payload = request_summary if request_summary is not None else request_payload
    if payload is not None:
        console.print("")
        console.print("Request JSON:")
        render_json_view(console, payload)

    response = response_summary if response_summary is not None else _summarize_response(response_payload)
    if response is not None:
        console.print("")
        console.print("Response summary:")
        render_json_view(console, response)

    if selected_ids:
        console.print("")
        console.print("Selected IDs:")
        render_json_view(console, selected_ids)


def _summarize_response(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        return {"items": len(value)}
    if isinstance(value, dict):
        summary: dict[str, Any] = {}
        for key in ("status", "query", "mode", "job_id"):
            if key in value:
                summary[key] = value[key]
        if "evidence" in value and isinstance(value["evidence"], list):
            summary["evidence_count"] = len(value["evidence"])
        if "domains" in value and isinstance(value["domains"], list):
            summary["domains_count"] = len(value["domains"])
        return safe_json(summary or value)
    return str(value)
