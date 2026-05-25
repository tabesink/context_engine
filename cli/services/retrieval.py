"""Retrieval route wrappers."""

from __future__ import annotations

from typing import Any, Literal

from cli.api_client import ApiClient
from cli.query_payload import build_query_payload

RetrievalMode = Literal["auto", "semantic", "navigation", "hybrid"]


class RetrievalService:
    def __init__(self, client: ApiClient):
        self._client = client

    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        top_k: int,
        include_debug: bool = False,
        lightrag_domain_id: str | None = None,
    ) -> dict[str, Any]:
        payload = build_query_payload(
            query=query,
            mode=mode,
            top_k=top_k,
            include_debug=include_debug,
            lightrag_domain_id=lightrag_domain_id,
        )
        response = self._client.post("/query/retrieve", payload)
        return response if isinstance(response, dict) else {}

    def answer(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        top_k: int,
        include_debug: bool = False,
        lightrag_domain_id: str | None = None,
    ) -> dict[str, Any]:
        payload = build_query_payload(
            query=query,
            mode=mode,
            top_k=top_k,
            include_debug=include_debug,
            lightrag_domain_id=lightrag_domain_id,
        )
        response = self._client.post("/query/answer", payload)
        return response if isinstance(response, dict) else {}
