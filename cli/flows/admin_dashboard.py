"""Admin dashboard workflow."""

from __future__ import annotations

from collections import Counter
from typing import Any

from cli.screens.models import ScreenResult, ScreenSection


def load_admin_dashboard(client: Any) -> dict[str, Any]:
    return {
        "documents": client.get("/admin/documents"),
        "jobs": client.get("/jobs"),
        "query_logs": client.get("/admin/query-logs"),
    }


def build_admin_dashboard_screen(dashboard: dict[str, Any]) -> ScreenResult:
    document_counts = Counter(str(item.get("status", "unknown")) for item in dashboard["documents"])
    job_counts = Counter(str(item.get("status", "unknown")) for item in dashboard["jobs"])
    return ScreenResult(
        title="Admin Dashboard",
        api_group="admin",
        sections=[
            ScreenSection(
                title="Documents",
                rows=[{"status": key, "count": value} for key, value in sorted(document_counts.items())],
                columns=["status", "count"],
            ),
            ScreenSection(
                title="Jobs",
                rows=[{"status": key, "count": value} for key, value in sorted(job_counts.items())],
                columns=["status", "count"],
            ),
            ScreenSection(
                title="Recent Queries",
                rows=dashboard["query_logs"],
                columns=["created_at", "user", "query", "mode"],
            ),
        ],
        raw=dashboard,
    )
