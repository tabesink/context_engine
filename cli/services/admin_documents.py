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
        enable_toc_refinement: str = "auto",
    ) -> dict[str, Any]:
        fields: dict[str, str] = {}
        if enable_toc_refinement != "auto":
            fields["enable_toc_refinement"] = enable_toc_refinement
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

    def index_document(self, document_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/documents/{document_id}/index")
        return payload if isinstance(payload, dict) else {}

    def reindex_document(self, document_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/documents/{document_id}/reindex")
        return payload if isinstance(payload, dict) else {}

    def rebuild_structure(
        self,
        document_id: str,
        *,
        enable_toc_refinement: str = "auto",
        preserve_assets: bool = True,
    ) -> dict[str, Any]:
        payload = self._client.post(
            f"/admin/documents/{document_id}/rebuild-structure",
            {
                "enable_toc_refinement": enable_toc_refinement,
                "preserve_assets": preserve_assets,
            },
        )
        return payload if isinstance(payload, dict) else {}

    def reingest_lightrag(self, document_id: str) -> dict[str, Any]:
        payload = self._client.post(f"/admin/documents/{document_id}/reingest-lightrag")
        return payload if isinstance(payload, dict) else {}

    def delete_document(self, document_id: str) -> dict[str, Any]:
        payload = self._client.delete(f"/admin/documents/{document_id}")
        return payload if isinstance(payload, dict) else {}
