"""LightRAG route wrappers."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from cli.api_client import ApiClient


class LightRagService:
    def __init__(self, client: ApiClient):
        self._client = client

    def list_labels(self, domain_id: str = "default") -> list[dict[str, Any]] | list[str]:
        payload = self._client.get(f"/lightrag/domains/{domain_id}/graph/labels")
        return payload if isinstance(payload, list) else []

    def popular_labels(
        self,
        *,
        domain_id: str = "default",
        limit: int = 20,
    ) -> list[dict[str, Any]] | list[str]:
        payload = self._client.get(
            f"/lightrag/domains/{domain_id}/graph/labels/popular?{urlencode({'limit': limit})}"
        )
        return payload if isinstance(payload, list) else []

    def search_labels(
        self,
        *,
        domain_id: str = "default",
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]] | list[str]:
        payload = self._client.get(
            f"/lightrag/domains/{domain_id}/graph/labels/search?{urlencode({'q': query, 'limit': limit})}"
        )
        return payload if isinstance(payload, list) else []

    def get_graph(
        self,
        *,
        domain_id: str = "default",
        label: str,
        max_depth: int = 3,
        max_nodes: int = 1000,
    ) -> dict[str, Any]:
        payload = self._client.get(
            f"/lightrag/domains/{domain_id}/graphs?"
            f"{urlencode({'label': label, 'max_depth': max_depth, 'max_nodes': max_nodes})}"
        )
        return payload if isinstance(payload, dict) else {}
