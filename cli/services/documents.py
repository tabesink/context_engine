"""Document route wrappers."""

from __future__ import annotations

from typing import Any

from cli.api_client import ApiClient


class DocumentService:
    def __init__(self, client: ApiClient):
        self._client = client

    def list_documents(self) -> list[dict[str, Any]]:
        payload = self._client.get("/documents")
        return payload if isinstance(payload, list) else []

    def get_document(self, document_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}")
        return payload if isinstance(payload, dict) else {}

    def get_structure(self, document_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}/structure")
        return payload if isinstance(payload, dict) else {}

    def get_page(self, document_id: str, page_number: int) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}/pages/{page_number}")
        return payload if isinstance(payload, dict) else {}
