"""Admin document route wrappers."""

from __future__ import annotations

from typing import Any

from cli.api_client import ApiClient


class AdminDocumentService:
    def __init__(self, client: ApiClient):
        self._client = client

    def list_documents(self) -> list[dict[str, Any]]:
        payload = self._client.get("/admin/documents")
        return payload if isinstance(payload, list) else []

    def upload_document(
        self,
        filename: str,
        content: bytes,
        *,
        lightrag_domain_id: str | None = None,
    ) -> dict[str, Any]:
        fields: dict[str, str] = {}
        if lightrag_domain_id:
            fields["lightrag_domain_id"] = lightrag_domain_id
        kwargs = {"fields": fields} if fields else {}
        payload = self._client.post_file(
            "/admin/documents/upload",
            field_name="file",
            filename=filename,
            content=content,
            **kwargs,
        )
        return payload if isinstance(payload, dict) else {}

    def refresh_status(self, document_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/documents/{document_id}/refresh-status")
        return payload if isinstance(payload, dict) else {}

    def reingest(self, document_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/documents/{document_id}/reingest")
        return payload if isinstance(payload, dict) else {}

    def delete_document(self, document_id: str) -> dict[str, Any]:
        payload = self._client.delete(f"/admin/documents/{document_id}")
        return payload if isinstance(payload, dict) else {}
