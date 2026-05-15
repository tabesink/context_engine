"""Retrieval and answer screen builders."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def _evidence_rows(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(evidence, start=1):
        rows.append(
            {
                "#": index,
                "source": item.get("document_id", item.get("source_document_id", "")),
                "engine": item.get("source_engine", item.get("engine", "")),
                "score": item.get("score", ""),
                "pages": _page_range(item),
                "section": item.get("section", item.get("section_title", "")),
            }
        )
    return rows


def _page_range(item: dict[str, Any]) -> str:
    start = item.get("page_start", item.get("page_number", ""))
    end = item.get("page_end", "")
    if start and end and start != end:
        return f"{start}-{end}"
    return str(start or end or "")


def build_retrieval_screen(response: dict[str, Any]) -> ScreenResult:
    evidence = response.get("evidence") or response.get("sources") or []
    sections = [
        ScreenSection(
            title="Request",
            rows=[
                {"field": "Requested mode", "value": response.get("mode", "")},
                {"field": "Top K", "value": response.get("top_k", "")},
                {"field": "Document filter", "value": response.get("document_filter", "none")},
                {
                    "field": "General fallback",
                    "value": response.get("allow_general_fallback", False),
                },
                {"field": "Debug requested", "value": bool(response.get("debug"))},
            ],
            columns=["field", "value"],
        ),
        ScreenSection(
            title="Results",
            rows=_evidence_rows(evidence),
            columns=["#", "source", "engine", "score", "pages", "section"],
        )
    ]
    for index, item in enumerate(evidence, start=1):
        sections.append(
            ScreenSection(
                title=f"Evidence [{index}]",
                rows=[
                    {"field": "Evidence ID", "value": item.get("id", item.get("evidence_id", ""))},
                    {
                        "field": "Document",
                        "value": item.get("document_id", item.get("source_document_id", "")),
                    },
                    {
                        "field": "Source engine",
                        "value": item.get("source_engine", item.get("engine", "")),
                    },
                    {"field": "Score", "value": item.get("score", "")},
                    {"field": "Page", "value": _page_range(item)},
                    {"field": "Section", "value": item.get("section", item.get("section_title", ""))},
                ],
                columns=["field", "value"],
            )
        )
        text = item.get("text", item.get("content", ""))
        if text:
            sections.append(ScreenSection(title="Text", text=str(text)))
    if response.get("debug"):
        debug = response["debug"]
        sections.append(
            ScreenSection(
                title="Debug",
                rows=[{"field": key.replace("_", " ").title(), "value": value} for key, value in debug.items()],
                columns=["field", "value"],
            )
        )
    return ScreenResult(
        title="Retrieved Context",
        api_group="retrieval",
        summary={"query": response.get("query", "")},
        sections=sections,
        actions=[
            ScreenAction("Ask with answer", f"ragcli documents answer --query \"{response.get('query', '...')}\""),
            ScreenAction("Retrieve semantic", f"ragcli documents retrieve --query \"{response.get('query', '...')}\" --mode semantic --top-k 5"),
        ],
        raw=response,
    )


def build_answer_screen(response: dict[str, Any], *, title: str = "Answer") -> ScreenResult:
    evidence = response.get("evidence") or response.get("sources") or []
    return ScreenResult(
        title=title,
        api_group="retrieval",
        summary={"question": response.get("query", "")},
        sections=[
            ScreenSection(title="Answer", text=str(response.get("answer", ""))),
            ScreenSection(
                title="Sources",
                rows=_evidence_rows(evidence),
                columns=["#", "source", "pages", "section", "score"],
            ),
        ],
        actions=[
            ScreenAction(
                "Retrieve only",
                f"ragcli documents retrieve --query \"{response.get('query', '...')}\"",
            )
        ],
        raw=response,
    )
