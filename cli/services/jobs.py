"""Index job route wrappers."""

from __future__ import annotations

from typing import Any

from cli.api_client import ApiClient


class JobService:
    def __init__(self, client: ApiClient):
        self._client = client

    def list_jobs(self) -> list[dict[str, Any]]:
        payload = self._client.get("/jobs")
        return payload if isinstance(payload, list) else []

    def get_job(self, job_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/jobs/{job_id}")
        return payload if isinstance(payload, dict) else {}

    def retry_job(self, job_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/jobs/{job_id}/retry")
        return payload if isinstance(payload, dict) else {}
