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

    def get_structure(
        self,
        document_id: str,
        *,
        include_blocks: bool = False,
        include_assets: bool = False,
    ) -> dict[str, Any]:
        query = (
            f"?include_blocks={str(include_blocks).lower()}"
            f"&include_assets={str(include_assets).lower()}"
        )
        payload = self._client.get(f"/documents/{document_id}/structure{query}")
        return payload if isinstance(payload, dict) else {}

    def get_ingestion_status(self, document_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}/ingestion-status")
        return payload if isinstance(payload, dict) else {}

    def get_structure_quality(self, document_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}/structure-quality")
        return payload if isinstance(payload, dict) else {}

    def get_section(self, document_id: str, section_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}/sections/{section_id}")
        return payload if isinstance(payload, dict) else {}

    def get_chunk(self, document_id: str, chunk_id: str) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}/chunks/{chunk_id}")
        return payload if isinstance(payload, dict) else {}

    def list_chunks(self, document_id: str) -> list[dict[str, Any]]:
        payload = self._client.get(f"/documents/{document_id}/chunks")
        return payload if isinstance(payload, list) else []

    def list_assets(self, document_id: str) -> list[dict[str, Any]]:
        payload = self._client.get(f"/documents/{document_id}/assets")
        return payload if isinstance(payload, list) else []

    def get_page(self, document_id: str, page_number: int) -> dict[str, Any]:
        payload = self._client.get(f"/documents/{document_id}/pages/{page_number}")
        return payload if isinstance(payload, dict) else {}
