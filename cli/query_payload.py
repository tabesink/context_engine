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
) -> dict[str, Any]:
    request = QueryRequest(
        query=query,
        mode=mode,
        top_k=top_k,
        include_debug=include_debug,
        allow_general_fallback=allow_general_fallback,
        document_ids=document_ids,
    )
    payload = request.model_dump(mode="json")
    if payload.get("document_ids") is None:
        payload.pop("document_ids")
    return payload
