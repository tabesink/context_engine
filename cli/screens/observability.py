"""Observability screen builders for logs."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def build_audit_logs_screen(logs: list[dict[str, Any]]) -> ScreenResult:
    return ScreenResult(
        title="Audit Logs",
        api_group="observability",
        sections=[
            ScreenSection(
                title="",
                rows=logs,
                columns=["created_at", "user", "event", "status"],
            )
        ],
        actions=[ScreenAction("Query logs", "context-engine admin query-logs list")],
        raw=logs,
    )


def build_query_logs_screen(logs: list[dict[str, Any]]) -> ScreenResult:
    return ScreenResult(
        title="Query Logs",
        api_group="observability",
        sections=[
            ScreenSection(
                title="",
                rows=logs,
                columns=["created_at", "user", "mode", "top_k", "query"],
            )
        ],
        actions=[
            ScreenAction(
                "Retrieve with debug",
                'context-engine documents retrieve --query "reset procedure" --include-debug',
            )
        ],
        raw=logs,
    )
