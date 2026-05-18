"""Observability route wrappers."""

from __future__ import annotations

from typing import Any

from cli.api_client import ApiClient


class ObservabilityService:
    def __init__(self, client: ApiClient):
        self._client = client

    def query_logs(self) -> list[dict[str, Any]]:
        payload = self._client.get("/admin/query-logs")
        return payload if isinstance(payload, list) else []

    def audit_logs(self) -> list[dict[str, Any]]:
        payload = self._client.get("/admin/audit-logs")
        return payload if isinstance(payload, list) else []
