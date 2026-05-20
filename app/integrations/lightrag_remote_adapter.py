from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.domain.models import Evidence, PageRef, RetrievalMode
from app.integrations.lightrag_domains import resolve_lightrag_domain


class LightRAGAdapterError(Exception):
    status_code = status.HTTP_502_BAD_GATEWAY


class LightRAGAuthenticationError(LightRAGAdapterError):
    status_code = status.HTTP_502_BAD_GATEWAY


class LightRAGInvalidResponse(LightRAGAdapterError):
    status_code = status.HTTP_502_BAD_GATEWAY


class LightRAGServiceUnavailable(LightRAGAdapterError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class LightRAGUpstreamError(LightRAGAdapterError):
    status_code = status.HTTP_502_BAD_GATEWAY

    def __init__(self, message: str, *, upstream_status: int):
        super().__init__(message)
        self.upstream_status = upstream_status


def lightrag_http_exception(exc: LightRAGAdapterError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


class LightRAGRemoteAdapter:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        client: httpx.Client | None = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.lightrag_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.lightrag_api_key
        self.timeout_seconds = timeout_seconds or settings.lightrag_timeout_seconds
        self.client = client or httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds)

    @classmethod
    def for_domain(cls, domain: str | None = None) -> "LightRAGRemoteAdapter":
        resolved = resolve_lightrag_domain(domain=domain)
        return cls(base_url=resolved.base_url, api_key=resolved.api_key)

    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        top_k: int,
        document_ids: list[str] | None,
        domain: str | None = None,
    ) -> list[Evidence]:
        payload = {
            "query": query,
            "mode": self._lightrag_mode(mode),
            "top_k": top_k,
            "chunk_top_k": top_k,
            "include_references": True,
            "include_chunk_content": True,
        }
        if document_ids:
            payload["document_ids"] = document_ids
        if domain:
            payload["domain"] = domain

        response = self.post_json("/query/data", json=payload)
        data = response.get("data")
        if not isinstance(data, dict):
            raise LightRAGInvalidResponse("Invalid LightRAG query response")
        return self._evidence_from_query_data(data, top_k=top_k)

    def upload_document(
        self,
        *,
        file_path: Path,
        filename: str,
        content_type: str,
        metadata: dict | None = None,
        domain: str | None = None,
    ) -> dict[str, Any]:
        form_data: dict[str, str] = {}
        if domain:
            form_data["domain"] = domain
        if metadata:
            for key, value in metadata.items():
                form_data[f"metadata[{key}]"] = str(value)

        with file_path.open("rb") as handle:
            data = self.post_json(
                "/documents/upload",
                data=form_data,
                files={"file": (filename, handle, content_type)},
            )

        return {
            "document_id": data.get("document_id"),
            "track_id": data.get("track_id"),
            "status": self._normalize_upload_status(data.get("status")),
            "message": data.get("message"),
        }

    def document_status(self, track_id: str) -> dict[str, Any]:
        data = self.get_json(f"/documents/track_status/{track_id}")
        documents = data.get("documents") if isinstance(data, dict) else None
        first = documents[0] if isinstance(documents, list) and documents else {}
        return {
            "document_id": first.get("id"),
            "track_id": data.get("track_id", track_id),
            "status": self._normalize_status(first.get("status")),
            "error": first.get("error_msg"),
            "metadata": first.get("metadata") or {},
        }

    def get_json(self, path: str, *, params: dict | None = None) -> dict[str, Any] | list[Any]:
        return self._request_json("GET", path, params=params)

    def post_json(
        self,
        path: str,
        *,
        json: dict | None = None,
        data: dict | None = None,
        files: dict | None = None,
    ) -> dict[str, Any]:
        response = self._request_json("POST", path, json=json, data=data, files=files)
        if not isinstance(response, dict):
            raise LightRAGInvalidResponse("Invalid LightRAG response")
        return response

    def _request_json(self, method: str, path: str, **kwargs):
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        try:
            response = self.client.request(method, path, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise LightRAGServiceUnavailable("LightRAG service unavailable") from exc
        except httpx.ConnectError as exc:
            raise LightRAGServiceUnavailable("LightRAG service unavailable") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise LightRAGAuthenticationError("LightRAG authentication failed") from exc
            raise LightRAGUpstreamError(
                "LightRAG upstream request failed",
                upstream_status=exc.response.status_code,
            ) from exc
        except ValueError as exc:
            raise LightRAGInvalidResponse("Invalid LightRAG response") from exc

    def _evidence_from_query_data(self, data: dict[str, Any], *, top_k: int) -> list[Evidence]:
        chunks = data.get("chunks") or []
        references = {
            item.get("reference_id"): item
            for item in data.get("references", [])
            if isinstance(item, dict) and item.get("reference_id")
        }
        evidence: list[Evidence] = []
        for index, chunk in enumerate(chunks[:top_k]):
            if not isinstance(chunk, dict):
                continue
            reference = references.get(chunk.get("reference_id"), {})
            document_id = chunk.get("document_id") or reference.get("document_id") or chunk.get("file_path")
            evidence.append(
                Evidence(
                    id=str(chunk.get("chunk_id") or chunk.get("reference_id") or f"lightrag-{index}"),
                    document_id=self._document_uuid(document_id),
                    source_engine="lightrag",
                    text=str(chunk.get("content") or chunk.get("text") or ""),
                    score=chunk.get("score"),
                    page_ref=PageRef(
                        document_id=self._document_uuid(document_id),
                        page_start=chunk.get("page_start"),
                        page_end=chunk.get("page_end"),
                    ),
                    metadata={
                        "source_path": chunk.get("file_path") or reference.get("file_path"),
                        "reference_id": chunk.get("reference_id"),
                        "external_document_id": document_id,
                    },
                )
            )
        return evidence

    def _document_uuid(self, value: Any) -> UUID:
        if value:
            try:
                return UUID(str(value))
            except ValueError:
                return uuid5(NAMESPACE_URL, str(value))
        return uuid5(NAMESPACE_URL, "lightrag:unknown")

    def _lightrag_mode(self, mode: RetrievalMode) -> str:
        if mode in {RetrievalMode.SEMANTIC, RetrievalMode.HYBRID, RetrievalMode.AUTO}:
            return "mix"
        return "naive"

    def _normalize_upload_status(self, value: Any) -> str:
        """Map LightRAG upload/insert response status to app-facing ingestion state."""
        normalized = str(value or "").lower()
        if normalized in {"failed", "failure", "error"}:
            return "failed"
        # Upstream uses "success" / "duplicated" when the file is accepted; indexing continues async.
        if normalized in {"success", "duplicated", "scanning_started", "reprocessing_started"}:
            return "indexing"
        if normalized in {"processed", "ready", "complete", "completed"}:
            return "ready"
        return "indexing"

    def _normalize_status(self, value: Any) -> str:
        normalized = str(value or "").lower()
        if normalized in {"processed", "ready", "complete", "completed", "success"}:
            return "ready"
        if normalized in {"failed", "failure", "error"}:
            return "failed"
        return "indexing"
