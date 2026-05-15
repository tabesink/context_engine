"""Document screen builders."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def build_document_library_screen(
    documents: list[dict[str, Any]],
    *,
    base_url: str | None = None,
) -> ScreenResult:
    if not documents:
        return ScreenResult(
            title="Documents",
            api_group="documents",
            summary={"backend": base_url} if base_url else {},
            sections=[ScreenSection(title="No documents found", text="")],
            actions=[ScreenAction("Upload document", "ragcli admin documents upload --file ./manual.pdf")],
            raw=documents,
        )
    return ScreenResult(
        title="Documents",
        api_group="documents",
        summary={"backend": base_url} if base_url else {},
        sections=[
            ScreenSection(
                title="",
                rows=documents,
                columns=["id", "filename", "status", "pages", "updated_at"],
            )
        ],
        actions=[
            ScreenAction(
                "Show document",
                f"ragcli documents show --document-id {documents[0].get('id', '<id>')}",
            ),
            ScreenAction(
                "Retrieve evidence",
                f"ragcli documents retrieve --query \"reset procedure\" --document-id {documents[0].get('id', '<id>')}",
            ),
        ],
        raw=documents,
    )


def build_document_detail_screen(document: dict[str, Any]) -> ScreenResult:
    document_id = document.get("id", document.get("document_id", "<id>"))
    return ScreenResult(
        title="Document Detail",
        api_group="documents",
        sections=[
            ScreenSection(
                title="",
                rows=[
                    {"field": "Document ID", "value": document_id},
                    {"field": "Filename", "value": document.get("filename", "")},
                    {"field": "Status", "value": document.get("status", "")},
                    {"field": "Pages", "value": document.get("pages", "")},
                    {"field": "Created", "value": document.get("created_at", "")},
                    {"field": "Updated", "value": document.get("updated_at", "")},
                ],
                columns=["field", "value"],
            )
        ],
        actions=[
            ScreenAction("Structure", f"ragcli documents structure --document-id {document_id}"),
            ScreenAction("Page", f"ragcli documents page --document-id {document_id} --page-number 1"),
            ScreenAction("Retrieve", f"ragcli documents retrieve --query \"your question\" --document-id {document_id}"),
        ],
        raw=document,
    )


def build_document_structure_screen(structure: dict[str, Any]) -> ScreenResult:
    tree = structure.get("tree", structure)
    rows = _structure_rows(tree)
    sections = (
        [ScreenSection(title="", rows=rows, columns=["level", "title", "pages"])]
        if rows
        else [ScreenSection(title="Structure", text=str(tree))]
    )
    return ScreenResult(
        title="Document Structure",
        api_group="documents",
        summary={"document_id": structure.get("document_id", "")},
        sections=sections,
        actions=[
            ScreenAction(
                "Open page",
                f"ragcli documents page --document-id {structure.get('document_id', '<id>')} --page-number 1",
            ),
            ScreenAction(
                "Retrieve section",
                f"ragcli documents retrieve --query \"Pendant Reset\" --document-id {structure.get('document_id', '<id>')}",
            ),
        ],
        raw=structure,
    )


def build_document_page_screen(page: dict[str, Any]) -> ScreenResult:
    document_id = page.get("document_id", "")
    page_number = page.get("page_number", "")
    return ScreenResult(
        title="Document Page",
        api_group="documents",
        sections=[
            ScreenSection(
                title="",
                rows=[
                    {"field": "Document ID", "value": document_id},
                    {"field": "Filename", "value": page.get("filename", "")},
                    {"field": "Page", "value": page_number},
                    {"field": "Section", "value": page.get("section", "")},
                ],
                columns=["field", "value"],
            ),
            ScreenSection(title="Content", text=str(page.get("text", ""))),
        ],
        actions=[
            ScreenAction(
                "Previous page",
                f"ragcli documents page --document-id {document_id} --page-number {max(int(page_number or 1) - 1, 1)}",
            ),
            ScreenAction(
                "Next page",
                f"ragcli documents page --document-id {document_id} --page-number {int(page_number or 1) + 1}",
            ),
            ScreenAction(
                "Retrieve",
                f"ragcli documents retrieve --query \"pendant reset\" --document-id {document_id}",
            ),
        ],
        raw=page,
    )


def _structure_rows(tree: Any) -> list[dict[str, Any]]:
    if isinstance(tree, dict) and isinstance(tree.get("sections"), list):
        return [_structure_row(item) for item in tree["sections"]]
    if isinstance(tree, list):
        return [_structure_row(item) for item in tree]
    return []


def _structure_row(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"level": "", "title": str(item), "pages": ""}
    return {
        "level": item.get("level", ""),
        "title": item.get("title", ""),
        "pages": item.get("pages", item.get("page_range", "")),
    }
