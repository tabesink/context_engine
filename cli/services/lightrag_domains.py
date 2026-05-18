"""LightRAG domain deployment route wrappers."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from cli.api_client import ApiClient


class LightRAGDomainService:
    def __init__(self, client: ApiClient):
        self._client = client

    def list_user_domains(self) -> dict[str, Any]:
        payload = self._client.get("/lightrag/domains")
        return payload if isinstance(payload, dict) else {"domains": []}

    def list_admin_domains(self) -> dict[str, Any]:
        payload = self._client.get("/admin/lightrag/domains")
        return payload if isinstance(payload, dict) else {"domains": []}

    def create_domain(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post("/admin/lightrag/domains", payload)
        return response if isinstance(response, dict) else {}

    def show_domain(self, domain_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/admin/lightrag/domains/{domain_id}")
        return payload if isinstance(payload, dict) else {}

    def up_domain(self, domain_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/lightrag/domains/{domain_id}/up")
        return payload if isinstance(payload, dict) else {}

    def down_domain(self, domain_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/lightrag/domains/{domain_id}/down")
        return payload if isinstance(payload, dict) else {}

    def recreate_domain(self, domain_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/lightrag/domains/{domain_id}/recreate")
        return payload if isinstance(payload, dict) else {}

    def regenerate_domain(self, domain_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/lightrag/domains/{domain_id}/regenerate")
        return payload if isinstance(payload, dict) else {}

    def remove_domain(self, domain_id: str, *, permanent: bool = False) -> dict[str, Any]:
        query = f"?{urlencode({'permanent': 'true'})}" if permanent else ""
        payload = self._client.delete(f"/admin/lightrag/domains/{domain_id}{query}")
        return payload if isinstance(payload, dict) else {}
