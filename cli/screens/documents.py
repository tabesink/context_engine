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
            actions=[ScreenAction("Upload document", "context-engine admin documents upload --file ./manual.pdf")],
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
                f"context-engine documents show --document-id {documents[0].get('id', '<id>')}",
            ),
            ScreenAction(
                "Retrieve evidence",
                f"context-engine documents retrieve --query \"reset procedure\" --document-id {documents[0].get('id', '<id>')}",
            ),
        ],
        raw=documents,
    )


def build_document_detail_screen(
    document: dict[str, Any],
    *,
    structure_quality: dict[str, Any] | None = None,
) -> ScreenResult:
    document_id = document.get("id", document.get("document_id", "<id>"))
    sections = [
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
    ]
    if structure_quality:
        sections.append(
            ScreenSection(
                title="Structure Quality",
                rows=[
                    {"field": "Score", "value": structure_quality.get("score", "")},
                    {"field": "Sections", "value": structure_quality.get("section_count", "")},
                    {"field": "Blocks", "value": structure_quality.get("block_count", "")},
                    {"field": "Assets", "value": structure_quality.get("asset_count", "")},
                    {
                        "field": "TOC Refiner",
                        "value": str(structure_quality.get("should_run_toc_refiner", "")),
                    },
                ],
                columns=["field", "value"],
            )
        )
    return ScreenResult(
        title="Document Detail",
        api_group="documents",
        sections=sections,
        actions=[
            ScreenAction("Structure", f"context-engine documents structure --document-id {document_id}"),
            ScreenAction("Page", f"context-engine documents page --document-id {document_id} --page-number 1"),
            ScreenAction("Retrieve", f"context-engine documents retrieve --query \"your question\" --document-id {document_id}"),
            ScreenAction(
                "Rebuild structure",
                f"context-engine admin documents rebuild-structure --document-id {document_id}",
            ),
            ScreenAction(
                "Reingest LightRAG",
                f"context-engine admin documents reingest-lightrag --document-id {document_id}",
            ),
        ],
        raw=document,
    )


def build_document_structure_screen(structure: dict[str, Any]) -> ScreenResult:
    tree = structure.get("tree", structure)
    rows = _structure_rows(tree)
    summary = {"document_id": structure.get("document_id", "")}
    if structure.get("source"):
        summary.update(
            {
                "source": structure.get("source", ""),
                "sections": len(structure.get("sections") or []),
                "source_chunks": len(structure.get("source_chunks") or []),
                "assets": len(structure.get("assets") or []),
            }
        )
    sections = (
        [ScreenSection(title="", rows=rows, columns=["level", "title", "pages"])]
        if rows
        else [ScreenSection(title="Structure", text=str(tree))]
    )
    return ScreenResult(
        title="Document Structure",
        api_group="documents",
        summary=summary,
        sections=sections,
        actions=[
            ScreenAction(
                "Open page",
                f"context-engine documents page --document-id {structure.get('document_id', '<id>')} --page-number 1",
            ),
            ScreenAction(
                "Retrieve section",
                f"context-engine documents retrieve --query \"Pendant Reset\" --document-id {structure.get('document_id', '<id>')}",
            ),
        ],
        raw=structure,
    )


def build_document_section_screen(payload: dict[str, Any]) -> ScreenResult:
    section = payload.get("section") if isinstance(payload.get("section"), dict) else {}
    document_id = payload.get("document_id", section.get("document_id", ""))
    section_id = section.get("section_id", "")
    sections = [
        ScreenSection(
            title="",
            rows=[
                {"field": "Title", "value": section.get("title", "")},
                {"field": "Section ID", "value": section_id},
                {"field": "Level", "value": section.get("level", "")},
                {"field": "Pages", "value": _page_range(section)},
            ],
            columns=["field", "value"],
        )
    ]
    blocks = payload.get("blocks") or []
    if blocks:
        sections.append(
            ScreenSection(
                title="Blocks",
                rows=[
                    {
                        "block_id": block.get("block_id", ""),
                        "type": block.get("type", ""),
                        "text": block.get("text", ""),
                    }
                    for block in blocks
                    if isinstance(block, dict)
                ],
                columns=["block_id", "type", "text"],
            )
        )
    chunks = payload.get("source_chunks") or []
    if chunks:
        sections.append(
            ScreenSection(
                title="Source Chunks",
                rows=[
                    {
                        "chunk_id": chunk.get("chunk_id", ""),
                        "pages": _page_range(chunk),
                        "assets": len(chunk.get("asset_ids") or []),
                    }
                    for chunk in chunks
                    if isinstance(chunk, dict)
                ],
                columns=["chunk_id", "pages", "assets"],
            )
        )
    assets = payload.get("assets") or []
    if assets:
        sections.append(
            ScreenSection(
                title="Assets",
                rows=[
                    {
                        "asset_id": asset.get("asset_id", ""),
                        "type": asset.get("asset_type", ""),
                        "caption": asset.get("caption", ""),
                    }
                    for asset in assets
                    if isinstance(asset, dict)
                ],
                columns=["asset_id", "type", "caption"],
            )
        )
    return ScreenResult(
        title="Document Section",
        api_group="documents",
        summary={"document_id": document_id, "section_id": section_id},
        sections=sections,
        actions=[
            ScreenAction(
                "Open structure",
                f"context-engine documents structure --document-id {document_id}",
            ),
            ScreenAction(
                "Retrieve section",
                f"context-engine documents retrieve --query \"{section.get('title', 'section')}\" --document-id {document_id}",
            ),
        ],
        raw=payload,
    )


def build_document_chunk_screen(chunk: dict[str, Any]) -> ScreenResult:
    document_id = chunk.get("document_id", "")
    chunk_id = chunk.get("chunk_id", "")
    sections = [
        ScreenSection(
            title="",
            rows=[
                {"field": "Section ID", "value": chunk.get("section_id", "")},
                {"field": "Pages", "value": _page_range(chunk)},
                {"field": "Blocks", "value": ", ".join(chunk.get("block_ids") or [])},
                {"field": "Assets", "value": ", ".join(chunk.get("asset_ids") or [])},
            ],
            columns=["field", "value"],
        ),
        ScreenSection(title="Text", text=str(chunk.get("text", ""))),
    ]
    metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}
    if metadata:
        sections.append(
            ScreenSection(
                title="Metadata",
                rows=[
                    {
                        "field": key,
                        "value": ", ".join(value) if isinstance(value, list) else str(value),
                    }
                    for key, value in metadata.items()
                ],
                columns=["field", "value"],
            )
        )
    return ScreenResult(
        title="Source Chunk",
        api_group="documents",
        summary={"document_id": document_id, "chunk_id": chunk_id},
        sections=sections,
        actions=[
            ScreenAction(
                "Open structure",
                f"context-engine documents structure --document-id {document_id}",
            ),
            ScreenAction(
                "Retrieve similar",
                f"context-engine documents retrieve --query \"{str(chunk.get('text', ''))[:40]}\" --document-id {document_id}",
            ),
        ],
        raw=chunk,
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
                f"context-engine documents page --document-id {document_id} --page-number {max(int(page_number or 1) - 1, 1)}",
            ),
            ScreenAction(
                "Next page",
                f"context-engine documents page --document-id {document_id} --page-number {int(page_number or 1) + 1}",
            ),
            ScreenAction(
                "Retrieve",
                f"context-engine documents retrieve --query \"pendant reset\" --document-id {document_id}",
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
        "pages": item.get("pages") or item.get("page_range") or _page_range(item),
    }


def _page_range(item: dict[str, Any]) -> str:
    page_start = item.get("page_start")
    page_end = item.get("page_end")
    if page_start is None:
        return ""
    if page_end is None or page_end == page_start:
        return str(page_start)
    return f"{page_start}-{page_end}"
