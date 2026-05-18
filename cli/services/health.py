"""Health route wrappers."""

from __future__ import annotations

from typing import Any

from cli.api_client import ApiClient


class HealthService:
    def __init__(self, client: ApiClient):
        self._client = client

    def health(self) -> dict[str, Any]:
        payload = self._client.get("/health")
        return payload if isinstance(payload, dict) else {}

    def readiness(self) -> dict[str, Any]:
        payload = self._client.get("/health/readiness")
        return payload if isinstance(payload, dict) else {}
