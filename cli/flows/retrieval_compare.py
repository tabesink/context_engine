"""Retrieval mode comparison flow."""

from __future__ import annotations

from typing import Any

from cli.api_client import ApiClientError
from cli.retrieve_payload import build_retrieve_payload
from cli.screens.models import ScreenResult, ScreenSection

MODES = ["auto", "semantic", "navigation", "hybrid"]


def compare_retrieval_modes(client: Any, *, query: str, top_k: int) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for mode in MODES:
        try:
            response = client.post(
                "/retrieve",
                build_retrieve_payload(
                    query=query,
                    mode=mode,  # type: ignore[arg-type]
                    top_k=top_k,
                    include_debug=False,
                ),
            )
        except ApiClientError as exc:
            results.append({"mode": mode, "error": {"code": exc.code, "message": exc.message}})
            continue
        evidence = response.get("evidence") or []
        top_score = evidence[0].get("score", "") if evidence else ""
        results.append(
            {
                "mode": mode,
                "evidence": len(evidence),
                "top_score": top_score,
                "selected_engine": (response.get("debug") or {}).get(
                    "selected_engine",
                    response.get("mode", mode),
                ),
            }
        )
    return {"query": query, "top_k": top_k, "results": results}


def build_retrieval_compare_screen(comparison: dict[str, Any]) -> ScreenResult:
    return ScreenResult(
        title="Retrieval Mode Comparison",
        api_group="retrieval",
        summary={"Query": comparison["query"], "Top K": comparison["top_k"]},
        sections=[
            ScreenSection(
                title="Modes",
                rows=comparison["results"],
                columns=["mode", "evidence", "top_score", "selected_engine", "error"],
            )
        ],
        raw=comparison,
    )
