from typing import Any

from app.schemas.query import QueryRequest


def build_query_payload(
    *,
    query: str,
    mode: str,
    top_k: int,
    include_debug: bool,
    allow_general_fallback: bool,
    document_ids: list[str] | None = None,
    lightrag_domain_id: str | None = None,
    include_assets: bool | None = None,
    include_thumbnails: bool | None = None,
    max_assets: int | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "query": query,
        "mode": mode,
        "top_k": top_k,
        "include_debug": include_debug,
        "allow_general_fallback": allow_general_fallback,
        "document_ids": document_ids,
        "lightrag_domain_id": lightrag_domain_id,
    }
    if include_assets is not None:
        data["include_assets"] = include_assets
    if include_thumbnails is not None:
        data["include_thumbnails"] = include_thumbnails
    if max_assets is not None:
        data["max_assets"] = max_assets

    request = QueryRequest(**data)
    payload = request.model_dump(mode="json")
    if payload.get("document_ids") is None:
        payload.pop("document_ids")
    if payload.get("lightrag_domain_id") is None:
        payload.pop("lightrag_domain_id")
    if include_assets is None:
        payload.pop("include_assets")
    if include_thumbnails is None:
        payload.pop("include_thumbnails")
    if max_assets is None:
        payload.pop("max_assets")
    return payload
