from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, Awaitable, Callable

from .utils import Tokenizer, write_json

DOCLING_STRUCTURAL_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx"}
STRUCTURAL_METADATA_VERSION = "structural-chunking-v1"
ATOMIC_TOKEN_MULTIPLIER = 2
LAYOUT_FURNITURE_LABELS = {"page_header", "page_footer"}
SECTION_BLOCK_LABELS = {"section_header", "title"}
TOC_TABLE_LABEL = "document_index"
LLM_SECTION_WARNING_PREFIX = "LLM section refinement failed"
KG_EXTRACTABLE_BLOCK_TYPES = {"paragraph"}
ATOMIC_BLOCK_TYPES = {"table", "code", "figure", "caption"}
NON_SEMANTIC_BLOCK_TYPES = {"table", "code", "figure", "caption", "heading", "layout"}
INDEX_TOC_ROLE = "table_of_contents"
INDEX_FIGURE_LIST_ROLE = "figure_list"
INDEX_TABLE_LIST_ROLE = "table_list"
NON_SEMANTIC_STRUCTURAL_ROLES = {
    "toc",
    "figure_list",
    "table_list",
    "table",
    "figure",
    "caption",
    "layout",
    "code",
    "heading",
}


def is_docling_structural_extension(ext: str) -> bool:
    """Return True for file types that should use Docling structural parsing."""
    return ext.lower() in DOCLING_STRUCTURAL_EXTENSIONS


def domain_root_for_file(file_path: Path, working_dir: str | Path) -> Path:
    """Locate the domain root used for durable structural artifacts.

    Domain deployments mount files under `data/domains/<domain>/...`. When a
    file comes from that layout, artifacts live beside the domain's inputs and
    rag_storage folders. For non-domain/local runs, the working directory parent
    is used so tests and simple local runs still have a deterministic location.
    """
    resolved = file_path.resolve()
    parts = resolved.parts
    if "data" in parts and "domains" in parts:
        domains_index = parts.index("domains")
        if domains_index + 1 < len(parts):
            return Path(*parts[: domains_index + 2])

    working_path = Path(working_dir).resolve()
    if working_path.name == "rag_storage":
        return working_path.parent
    return working_path


def artifact_paths_for_doc(file_path: Path, working_dir: str | Path, doc_id: str):
    """Return the domain root, artifact directory, and manifest-relative path."""
    domain_root = domain_root_for_file(file_path, working_dir)
    artifact_dir = domain_root / "artifacts" / doc_id
    relative_manifest = Path("artifacts") / doc_id / "manifest.json"
    return domain_root, artifact_dir, relative_manifest


def build_structural_artifacts(
    *,
    content: str,
    source_file: Path,
    working_dir: str | Path,
    doc_id: str,
    docling_document: Any | None = None,
    sections: list[dict[str, Any]] | None = None,
    extra_warnings: list[str] | None = None,
    extraction_error: str | None = None,
) -> dict[str, Any]:
    """Write a durable artifact manifest and return compact doc metadata.

    The compact metadata is designed for doc-status storage and queueing. The
    full block list is included under `structure` so the clean-slate pipeline can
    chunk immediately without re-reading the manifest, while the manifest remains
    the durable drill-down artifact for citations and later inspection.
    """
    _, artifact_dir, relative_manifest = artifact_paths_for_doc(source_file, working_dir, doc_id)
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    raw_docling = docling_document_to_dict(docling_document) if docling_document else {}
    blocks = build_docling_blocks(raw_docling) if raw_docling else normalize_markdown_blocks(content)
    toc_candidates = parse_docling_toc_candidates(raw_docling) if raw_docling else []
    sections = sections if sections is not None else build_sections_from_blocks(blocks, toc_candidates)
    _assign_sections_to_blocks(blocks, sections)
    warnings = [extraction_error] if extraction_error else []
    warnings.extend(extra_warnings or [])
    raw_docling_path = None
    if raw_docling:
        raw_docling_path = "docling_document.json"
        write_json(raw_docling, artifact_dir / raw_docling_path)

    manifest = {
        "version": STRUCTURAL_METADATA_VERSION,
        "doc_id": doc_id,
        "source_file": source_file.name,
        "source_engine": "docling",
        "content_rendering": "markdown",
        "manifest_path": str(relative_manifest),
        "status": "fallback_flat" if extraction_error else "structural",
        "warnings": warnings,
        "blocks": blocks,
        "sections": sections,
        "assets": [],
        "raw_docling_path": raw_docling_path,
    }
    write_json(manifest, artifact_dir / "manifest.json")

    return {
        "source_engine": "docling",
        "structure_status": manifest["status"],
        "structure_version": STRUCTURAL_METADATA_VERSION,
        "artifact_manifest_path": str(relative_manifest),
        "artifact_root": str(relative_manifest.parent),
        "page_count": _page_count(blocks),
        "block_count": len(blocks),
        "section_count": len(_flatten_sections(sections)),
        "warnings": manifest["warnings"],
        "structure": {"blocks": blocks, "sections": sections},
    }


async def build_llm_refined_sections(
    *,
    blocks: list[dict[str, Any]],
    toc_candidates: list[dict[str, Any]],
    headings: list[dict[str, Any]],
    llm_model_func: Callable[..., Awaitable[str]],
) -> list[dict[str, Any]]:
    """Ask the configured LLM for a compact PageIndex-style section tree."""
    prompt = _llm_section_prompt(blocks, toc_candidates, headings)
    response = await llm_model_func(prompt, max_tokens=2048)
    return validate_section_tree(_extract_json_object(response), blocks)


def should_refine_sections_with_llm(
    blocks: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    toc_candidates: list[dict[str, Any]],
) -> bool:
    """Return True when deterministic structure is too weak for navigation."""
    chunkable_blocks = [block for block in blocks if block.get("chunkable", True)]
    if not chunkable_blocks:
        return False
    if len(_flatten_sections(sections)) < 2:
        return True
    sectioned_block_count = sum(1 for block in chunkable_blocks if block.get("section_node_id"))
    return bool(toc_candidates) and sectioned_block_count < max(2, len(chunkable_blocks) // 3)


def normalize_markdown_blocks(markdown: str) -> list[dict[str, Any]]:
    """Normalize Markdown into structure-like blocks for v1 chunking.

    Docling's rendered Markdown keeps headings, tables, and code blocks even when
    the exact Docling object model changes between versions. This normalizer is
    intentionally conservative: it captures stable structure first and leaves
    page/image enrichment to later Docling-specific adapters.
    """
    blocks: list[dict[str, Any]] = []
    section_path: list[str] = []
    lines = markdown.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            section_path = section_path[: level - 1] + [title]
            blocks.append(_block("heading", stripped, len(blocks), section_path))
            index += 1
            continue

        if stripped.startswith("```"):
            block_lines = [line]
            index += 1
            while index < len(lines):
                block_lines.append(lines[index])
                if lines[index].strip().startswith("```"):
                    index += 1
                    break
                index += 1
            blocks.append(_block("code", "\n".join(block_lines), len(blocks), section_path))
            continue

        if _is_table_row(stripped):
            block_lines = [line]
            index += 1
            while index < len(lines) and _is_table_row(lines[index].strip()):
                block_lines.append(lines[index])
                index += 1
            blocks.append(_block("table", "\n".join(block_lines), len(blocks), section_path))
            continue

        block_lines = [line]
        index += 1
        while index < len(lines):
            next_stripped = lines[index].strip()
            if (
                not next_stripped
                or re.match(r"^(#{1,6})\s+(.+)$", next_stripped)
                or next_stripped.startswith("```")
                or _is_table_row(next_stripped)
            ):
                break
            block_lines.append(lines[index])
            index += 1
        blocks.append(_block("paragraph", "\n".join(block_lines).strip(), len(blocks), section_path))

    return blocks


def build_docling_blocks(raw_docling: dict[str, Any]) -> list[dict[str, Any]]:
    """Build manifest blocks from Docling's ordered document tree."""
    if not raw_docling:
        return []

    by_ref = _docling_ref_index(raw_docling)
    blocks: list[dict[str, Any]] = []
    section_path: list[str] = []
    for ref in _walk_docling_refs(raw_docling.get("body", {}).get("children", []), by_ref):
        item = by_ref.get(ref)
        if not isinstance(item, dict):
            continue
        block = _docling_item_to_block(item, ref, len(blocks), section_path, by_ref)
        if not block:
            continue
        if block["type"] == "heading":
            section_path = [block["text"]]
            block["section_path"] = list(section_path)
        else:
            block["section_path"] = list(section_path)
        blocks.append(block)

    toc_candidates = parse_docling_toc_candidates(raw_docling)
    sections = build_sections_from_blocks(blocks, toc_candidates)
    _assign_sections_to_blocks(blocks, sections)
    return blocks


def parse_docling_toc_candidates(raw_docling: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract major-section candidates from Docling TOC-like tables."""
    candidates: list[dict[str, Any]] = []
    for table in raw_docling.get("tables") or []:
        row_candidates = _toc_candidates_from_table(table)
        table_text = _table_text(table)
        structural_role = _table_structural_role(table.get("label") or "table", table_text)
        if structural_role in {"figure_list", "table_list"}:
            continue
        if table.get("label") != TOC_TABLE_LABEL and not _is_toc_like_table(table, row_candidates):
            continue
        candidates.extend(row_candidates)
    return _dedupe_toc_candidates(candidates)


def build_sections_from_blocks(
    blocks: list[dict[str, Any]],
    toc_candidates: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Create major sections from TOC entries, then headings, then page spans."""
    toc_sections = _sections_from_toc(blocks, toc_candidates or [])
    if toc_sections:
        _assign_sections_to_blocks(blocks, toc_sections)
        return toc_sections

    heading_sections = _sections_from_headings(blocks)
    if heading_sections:
        _assign_sections_to_blocks(blocks, heading_sections)
        return heading_sections

    fallback = _fallback_sections_from_pages(blocks)
    _assign_sections_to_blocks(blocks, fallback)
    return fallback


def validate_section_tree(
    section_tree: Any,
    blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate and normalize LLM-produced section JSON."""
    if isinstance(section_tree, dict):
        raw_sections = section_tree.get("sections") or section_tree.get("structure") or []
    else:
        raw_sections = section_tree
    if not isinstance(raw_sections, list):
        raise ValueError("section tree must be a list or object with sections")

    valid_block_ids = {block["id"] for block in blocks}
    normalized = [
        _normalize_section_node(node, index, valid_block_ids)
        for index, node in enumerate(raw_sections, 1)
        if isinstance(node, dict)
    ]
    normalized = [node for node in normalized if node.get("block_ids")]
    if not normalized:
        raise ValueError("section tree did not include any valid block links")
    _assign_sections_to_blocks(blocks, normalized)
    return normalized


def chunking_by_doc_structure(
    tokenizer: Tokenizer,
    content: str,
    document_metadata: dict[str, Any] | None,
    max_token_size: int = 1024,
) -> list[dict[str, Any]]:
    """Create balanced structure-aware chunks from normalized document blocks."""
    metadata = document_metadata or {}
    blocks = ((metadata.get("structure") or {}).get("blocks") or [])
    if not blocks:
        return []

    chunks: list[dict[str, Any]] = []
    current_blocks: list[dict[str, Any]] = []
    current_tokens = 0
    current_section: tuple[str, ...] | None = None

    def flush() -> None:
        nonlocal current_blocks, current_tokens, current_section
        if current_blocks:
            chunks.append(_chunk_from_blocks(tokenizer, current_blocks, metadata, len(chunks)))
        current_blocks = []
        current_tokens = 0
        current_section = None

    for block in blocks:
        if not block.get("chunkable", True):
            continue
        text = (block.get("text") or "").strip()
        if not text:
            continue
        block_type = block.get("type", "paragraph")
        block_tokens = len(tokenizer.encode(text))
        block_section = tuple(block.get("section_path") or [])

        structural_role = block.get("structural_role")
        if block_type in {"table", "code", "figure", "caption"} or structural_role in NON_SEMANTIC_STRUCTURAL_ROLES:
            flush()
            if block_tokens <= max_token_size * ATOMIC_TOKEN_MULTIPLIER:
                chunks.append(_chunk_from_blocks(tokenizer, [block], metadata, len(chunks)))
            else:
                chunks.extend(_split_oversized_atomic_block(tokenizer, block, metadata, len(chunks), max_token_size))
            continue

        if block_tokens > max_token_size:
            flush()
            chunks.extend(_split_text_block(tokenizer, block, metadata, len(chunks), max_token_size))
            continue

        if current_section is not None and block_section != current_section:
            flush()
        elif current_tokens + block_tokens > max_token_size:
            flush()

        current_blocks.append(block)
        current_tokens += block_tokens
        current_section = block_section

    flush()
    return chunks


def docling_document_to_dict(document: Any) -> dict[str, Any]:
    """Best-effort conversion of Docling documents into JSON-safe data."""
    if isinstance(document, dict):
        return _json_safe(document)
    for method_name in ("export_to_dict", "model_dump", "dict"):
        method = getattr(document, method_name, None)
        if callable(method):
            try:
                data = method()
                if isinstance(data, dict):
                    return _json_safe(data)
            except TypeError:
                continue
    return {}


def _docling_ref_index(raw_docling: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_ref: dict[str, dict[str, Any]] = {}
    for collection in ("texts", "tables", "pictures", "groups"):
        for item in raw_docling.get(collection) or []:
            ref = item.get("self_ref")
            if ref:
                by_ref[ref] = item
    return by_ref


def _walk_docling_refs(children: list[dict[str, Any]], by_ref: dict[str, dict[str, Any]]):
    for child in children or []:
        ref = child.get("$ref") if isinstance(child, dict) else None
        if not ref:
            continue
        item = by_ref.get(ref)
        if isinstance(item, dict) and item.get("children") and item.get("label") != "picture":
            yield from _walk_docling_refs(item.get("children") or [], by_ref)
        elif item:
            yield ref


def _docling_item_to_block(
    item: dict[str, Any],
    ref: str,
    index: int,
    section_path: list[str],
    by_ref: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    label = item.get("label") or "text"
    text = _docling_item_text(item, by_ref)
    if not text and label != "picture":
        return None
    pages = _prov_pages(item.get("prov") or [])
    block_type = _docling_block_type(label)
    structural_role = _docling_structural_role(label, block_type, text)
    return {
        "id": f"block-{index:05d}",
        "type": block_type,
        "label": label,
        "structural_role": structural_role,
        "navigation_kind": "structure" if structural_role in NON_SEMANTIC_STRUCTURAL_ROLES else "prose",
        "text": text,
        "page_start": min(pages) if pages else None,
        "page_end": max(pages) if pages else None,
        "section_path": list(section_path),
        "section_node_id": None,
        "artifact_refs": [],
        "docling_refs": [ref],
        "chunkable": label not in LAYOUT_FURNITURE_LABELS,
        "kg_extractable": _is_kg_extractable_block(block_type, label, structural_role),
    }


def _docling_item_text(item: dict[str, Any], by_ref: dict[str, dict[str, Any]] | None = None) -> str:
    if item.get("label") == "picture":
        text_candidates: list[str] = []
        for key in ("caption", "text", "orig"):
            value = item.get(key)
            if value:
                text_candidates.append(str(value).strip())
        for ref in _refs_from_items((item.get("captions") or []) + (item.get("children") or [])):
            child = (by_ref or {}).get(ref)
            if child:
                child_text = (child.get("text") or child.get("orig") or "").strip()
                if child_text:
                    text_candidates.append(child_text)
        text = " ".join(value for value in text_candidates if value).strip()
        return text or "[Picture]"
    if "data" in item and (item.get("data") or {}).get("table_cells"):
        return _table_cells_to_markdown((item.get("data") or {}).get("table_cells") or [])
    return (item.get("text") or item.get("orig") or "").strip()


def _docling_block_type(label: str) -> str:
    if label in SECTION_BLOCK_LABELS:
        return "heading"
    if label == "code":
        return "code"
    if label in {"table", TOC_TABLE_LABEL}:
        return "table"
    if label == "picture":
        return "figure"
    if label == "caption":
        return "caption"
    if label == "list_item":
        return "paragraph"
    if label in LAYOUT_FURNITURE_LABELS:
        return "layout"
    return "paragraph"


def _is_kg_extractable_block(
    block_type: str,
    label: str | None = None,
    structural_role: str | None = None,
) -> bool:
    if label in {TOC_TABLE_LABEL, *LAYOUT_FURNITURE_LABELS}:
        return False
    if structural_role in NON_SEMANTIC_STRUCTURAL_ROLES:
        return False
    return block_type in KG_EXTRACTABLE_BLOCK_TYPES


def _table_cells_to_markdown(cells: list[dict[str, Any]]) -> str:
    rows: dict[int, dict[int, str]] = {}
    max_col = 0
    for cell in cells:
        row = int(cell.get("start_row_offset_idx", 0))
        col = int(cell.get("start_col_offset_idx", 0))
        rows.setdefault(row, {})[col] = (cell.get("text") or "").strip()
        max_col = max(max_col, col)
    if not rows:
        return ""
    lines = []
    for row_index in sorted(rows):
        values = [rows[row_index].get(col, "") for col in range(max_col + 1)]
        lines.append("| " + " | ".join(values) + " |")
        if row_index == min(rows):
            lines.append("| " + " | ".join("---" for _ in range(max_col + 1)) + " |")
    return "\n".join(lines)


def _table_text(table: dict[str, Any]) -> str:
    return _table_cells_to_markdown((table.get("data") or {}).get("table_cells") or [])


def _docling_structural_role(label: str, block_type: str, text: str) -> str:
    if label in LAYOUT_FURNITURE_LABELS:
        return "layout"
    if label == TOC_TABLE_LABEL:
        return _table_structural_role(label, text)
    if label == "caption":
        return "caption"
    if label == "picture" or block_type == "figure":
        return "figure"
    if block_type == "table":
        return _table_structural_role(label, text)
    if block_type == "code":
        return "code"
    if block_type == "heading":
        return "heading"
    return "prose"


def _table_structural_role(label: str, text: str) -> str:
    if _looks_like_figure_list(text):
        return "figure_list"
    if _looks_like_table_list(text):
        return "table_list"
    if label == TOC_TABLE_LABEL:
        return "toc"
    return "table"


def _looks_like_figure_list(text: str) -> bool:
    return len(re.findall(r"\bfig(?:ure)?\.?\s*\d", text, flags=re.IGNORECASE)) >= 2


def _looks_like_table_list(text: str) -> bool:
    return len(re.findall(r"\btable\s+\d", text, flags=re.IGNORECASE)) >= 2


def _refs_from_items(items: list[dict[str, Any]]) -> list[str]:
    refs = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ref = item.get("$ref")
        if ref:
            refs.append(str(ref))
    return refs


def _prov_pages(prov: list[dict[str, Any]]) -> list[int]:
    return [int(item["page_no"]) for item in prov if item.get("page_no") is not None]


def _toc_candidate_from_cells(texts: list[str]) -> dict[str, Any] | None:
    joined = _normalize_toc_row_text(" ".join(texts))
    page_match = re.search(r"(?:page\s*)?(\d{1,4})\s*$", joined, flags=re.IGNORECASE)
    if not page_match:
        return None
    page = int(page_match.group(1))
    title_text = joined[: page_match.start()].strip(" .:")
    match = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", title_text)
    number = match.group(1) if match else None
    title_source = match.group(2) if match else title_text
    title = re.sub(r"\.{2,}", " ", title_source).strip(" .:")
    if not title:
        return None
    candidate = {
        "title": title,
        "page_start": page,
        "page_end": page,
    }
    if number:
        candidate["number"] = number
    return candidate


def _toc_candidates_from_table(table: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    rows: dict[int, list[dict[str, Any]]] = {}
    for cell in ((table.get("data") or {}).get("table_cells") or []):
        rows.setdefault(int(cell.get("start_row_offset_idx", 0)), []).append(cell)
    for row_index in sorted(rows):
        texts = [
            (cell.get("text") or "").strip()
            for cell in sorted(rows[row_index], key=lambda c: c.get("start_col_offset_idx", 0))
            if (cell.get("text") or "").strip()
        ]
        candidate = _toc_candidate_from_cells(texts)
        if candidate:
            candidate["docling_refs"] = [table.get("self_ref")]
            candidates.append(candidate)
    return candidates


def _is_toc_like_table(table: dict[str, Any], candidates: list[dict[str, Any]]) -> bool:
    if table.get("label") == TOC_TABLE_LABEL:
        return True
    row_count = len(
        {
            int(cell.get("start_row_offset_idx", 0))
            for cell in ((table.get("data") or {}).get("table_cells") or [])
        }
    )
    return len(candidates) >= 2 and len(candidates) >= max(2, row_count // 2)


def _normalize_toc_row_text(value: str) -> str:
    value = re.sub(r"\.{2,}", " ", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+:\s+", ": ", value)
    return value.strip()


def _toc_candidate_depth(candidate: dict[str, Any]) -> int:
    number = str(candidate.get("number") or "")
    return number.count(".") + 1 if number else 1


def _dedupe_toc_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, int | None]] = set()
    deduped = []
    for candidate in candidates:
        key = (candidate.get("number", ""), candidate.get("title", ""), candidate.get("page_start"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _sections_from_headings(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    headings = [block for block in blocks if block.get("type") == "heading" and block.get("chunkable", True)]
    sections = []
    for index, heading in enumerate(headings, 1):
        start = _block_position(blocks, heading["id"])
        end = _block_position(blocks, headings[index]["id"]) - 1 if index < len(headings) else len(blocks) - 1
        span = [block for block in blocks[start : end + 1] if block.get("chunkable", True)]
        sections.append(_section_from_span(index, heading.get("text") or f"Section {index}", span))
    return sections


def _sections_from_toc(
    blocks: list[dict[str, Any]],
    toc_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    stack: list[tuple[int, dict[str, Any]]] = []
    chunkable_blocks = [block for block in blocks if block.get("chunkable", True)]
    for index, candidate in enumerate(toc_candidates, 1):
        page_start = candidate.get("page_start")
        if page_start is None:
            continue
        next_page = _next_toc_page(toc_candidates, index)
        span = [
            block
            for block in chunkable_blocks
            if block.get("page_start") is not None
            and block["page_start"] >= page_start
            and (next_page is None or block["page_start"] < next_page)
        ]
        if not span:
            continue
        section = _section_from_span(index, candidate["title"], span, candidate)
        depth = _toc_candidate_depth(candidate)
        if depth > 1:
            while stack and stack[-1][0] >= depth:
                stack.pop()
            if stack:
                stack[-1][1].setdefault("nodes", []).append(section)
            else:
                sections.append(section)
            stack.append((depth, section))
        else:
            sections.append(section)
            stack = [(depth, section)]
    return sections


def _fallback_sections_from_pages(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunkable_blocks = [block for block in blocks if block.get("chunkable", True)]
    pages = sorted({block.get("page_start") for block in chunkable_blocks if block.get("page_start") is not None})
    if pages:
        return [
            _section_from_span(
                index,
                f"Page {page}",
                [block for block in chunkable_blocks if block.get("page_start") == page],
            )
            for index, page in enumerate(pages, 1)
        ]
    return [_section_from_span(1, "Document", chunkable_blocks)] if chunkable_blocks else []


def _section_from_span(
    index: int,
    title: str,
    span: list[dict[str, Any]],
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    block_ids = [block["id"] for block in span if block.get("id")]
    pages = [
        page
        for block in span
        for page in (block.get("page_start"), block.get("page_end"))
        if page is not None
    ]
    docling_refs = _collect_docling_refs(span)
    if candidate:
        docling_refs.extend(ref for ref in candidate.get("docling_refs") or [] if ref not in docling_refs)
    return {
        "node_id": f"sec-{index:04d}",
        "title": title.strip() or f"Section {index}",
        "summary": "",
        "page_start": min(pages) if pages else None,
        "page_end": max(pages) if pages else None,
        "block_ids": block_ids,
        "docling_refs": docling_refs,
        "nodes": [],
    }


def _assign_sections_to_blocks(blocks: list[dict[str, Any]], sections: list[dict[str, Any]]) -> None:
    by_id = {block.get("id"): block for block in blocks}
    for section in _flatten_sections(sections):
        path = _section_path_for_node(section, sections)
        for block_id in section.get("block_ids") or []:
            block = by_id.get(block_id)
            if not block:
                continue
            block["section_node_id"] = section.get("node_id")
            block["section_path"] = path


def _section_path_for_node(target: dict[str, Any], sections: list[dict[str, Any]]) -> list[str]:
    path: list[str] = []

    def visit(nodes: list[dict[str, Any]], trail: list[str]) -> bool:
        for node in nodes:
            next_trail = trail + [node.get("title", "")]
            if node is target or node.get("node_id") == target.get("node_id"):
                path.extend(title for title in next_trail if title)
                return True
            if visit(node.get("nodes") or [], next_trail):
                return True
        return False

    visit(sections, [])
    return path


def _block_position(blocks: list[dict[str, Any]], block_id: str) -> int:
    for index, block in enumerate(blocks):
        if block.get("id") == block_id:
            return index
    return 0


def _next_toc_page(candidates: list[dict[str, Any]], index: int) -> int | None:
    for candidate in candidates[index:]:
        if candidate.get("page_start") is not None:
            return candidate["page_start"]
    return None


def _normalize_section_node(
    node: dict[str, Any],
    index: int,
    valid_block_ids: set[str],
) -> dict[str, Any]:
    block_ids = [block_id for block_id in node.get("block_ids", []) if block_id in valid_block_ids]
    children = [
        _normalize_section_node(child, child_index, valid_block_ids)
        for child_index, child in enumerate(node.get("nodes") or [], 1)
        if isinstance(child, dict)
    ]
    children = [child for child in children if child.get("block_ids")]
    return {
        "node_id": str(node.get("node_id") or f"sec-{index:04d}"),
        "title": str(node.get("title") or f"Section {index}").strip(),
        "summary": str(node.get("summary") or "").strip(),
        "page_start": node.get("page_start"),
        "page_end": node.get("page_end"),
        "block_ids": block_ids,
        "docling_refs": [str(ref) for ref in node.get("docling_refs") or []],
        "nodes": children,
    }


def _extract_json_object(response: str) -> Any:
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(1))


def _llm_section_prompt(
    blocks: list[dict[str, Any]],
    toc_candidates: list[dict[str, Any]],
    headings: list[dict[str, Any]],
) -> str:
    outline = []
    for block in blocks:
        if not block.get("chunkable", True):
            continue
        outline.append(
            {
                "id": block.get("id"),
                "type": block.get("type"),
                "label": block.get("label"),
                "page_start": block.get("page_start"),
                "page_end": block.get("page_end"),
                "snippet": (block.get("text") or "")[:240],
            }
        )
    payload = {
        "toc_candidates": toc_candidates[:80],
        "detected_headings": headings[:80],
        "block_outline": outline[:250],
    }
    return (
        "Create a PageIndex-style major-section tree for this document. "
        "Return only JSON with a top-level sections array. Each section must "
        "include node_id, title, summary, page_start, page_end, block_ids, "
        "docling_refs, and nodes. Use only block_ids from the outline. "
        "Do not create figure/table-only sections.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def _block(block_type: str, text: str, index: int, section_path: list[str]) -> dict[str, Any]:
    structural_role = _docling_structural_role("", block_type, text)
    return {
        "id": f"block-{index:05d}",
        "type": block_type,
        "structural_role": structural_role,
        "navigation_kind": "structure" if structural_role in NON_SEMANTIC_STRUCTURAL_ROLES else "prose",
        "text": text,
        "page_start": None,
        "page_end": None,
        "section_path": list(section_path),
        "artifact_refs": [],
        "kg_extractable": _is_kg_extractable_block(block_type, structural_role=structural_role),
    }


def _chunk_from_blocks(
    tokenizer: Tokenizer,
    blocks: list[dict[str, Any]],
    document_metadata: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    content = "\n\n".join((block.get("text") or "").strip() for block in blocks).strip()
    first = blocks[0]
    last = blocks[-1]
    block_ids = [block.get("id") for block in blocks if block.get("id")]
    page_start = _first_present(block.get("page_start") for block in blocks)
    page_end = _last_present(block.get("page_end") for block in blocks)
    section_path = first.get("section_path") or []
    section_node_ids = _collect_unique(block.get("section_node_id") for block in blocks)
    chunk_type = first.get("type", "text") if len(blocks) == 1 else "section"
    kg_extractable = any(block.get("kg_extractable", True) for block in blocks)
    structural_roles = _collect_unique(block.get("structural_role") for block in blocks)
    labels = _collect_unique(block.get("label") for block in blocks)

    return {
        "tokens": len(tokenizer.encode(content)),
        "content": content,
        "chunk_order_index": index,
        "structural_id": ":".join(
            [
                str(document_metadata.get("artifact_manifest_path", "")),
                str(first.get("id", index)),
                str(last.get("id", index)),
                str(index),
            ]
        ),
        "page_start": page_start,
        "page_end": page_end,
        "section_path": " > ".join(section_path),
        "chunk_type": chunk_type,
        "kg_extractable": kg_extractable,
        "artifact_manifest_path": document_metadata.get("artifact_manifest_path"),
        "chunk_metadata": {
            "block_ids": block_ids,
            "artifact_refs": _collect_artifact_refs(blocks),
            "docling_refs": _collect_docling_refs(blocks),
            "labels": labels,
            "structural_roles": structural_roles,
            "section_node_ids": section_node_ids,
            "section_node_id": section_node_ids[0] if len(section_node_ids) == 1 else None,
            "kg_extractable": kg_extractable,
            "source_engine": document_metadata.get("source_engine"),
            "structure_status": document_metadata.get("structure_status"),
            "structure_version": document_metadata.get("structure_version"),
            "warnings": document_metadata.get("warnings", []),
        },
    }


def _split_text_block(
    tokenizer: Tokenizer,
    block: dict[str, Any],
    document_metadata: dict[str, Any],
    start_index: int,
    max_token_size: int,
) -> list[dict[str, Any]]:
    tokens = tokenizer.encode(block.get("text") or "")
    chunks = []
    for offset, start in enumerate(range(0, len(tokens), max_token_size)):
        split_block = {
            **block,
            "id": f"{block.get('id')}-part-{offset}",
            "text": tokenizer.decode(tokens[start : start + max_token_size]).strip(),
        }
        chunks.append(_chunk_from_blocks(tokenizer, [split_block], document_metadata, start_index + offset))
    return chunks


def _split_oversized_atomic_block(
    tokenizer: Tokenizer,
    block: dict[str, Any],
    document_metadata: dict[str, Any],
    start_index: int,
    max_token_size: int,
) -> list[dict[str, Any]]:
    lines = (block.get("text") or "").splitlines()
    if block.get("type") != "table" or len(lines) <= 2:
        return _split_text_block(tokenizer, block, document_metadata, start_index, max_token_size)

    header = lines[:2]
    rows = lines[2:]
    chunks = []
    current_rows: list[str] = []
    current_tokens = len(tokenizer.encode("\n".join(header)))
    for row in rows:
        row_tokens = len(tokenizer.encode(row))
        if current_rows and current_tokens + row_tokens > max_token_size:
            chunks.append(_atomic_split_chunk(tokenizer, block, document_metadata, start_index + len(chunks), header + current_rows))
            current_rows = []
            current_tokens = len(tokenizer.encode("\n".join(header)))
        current_rows.append(row)
        current_tokens += row_tokens
    if current_rows:
        chunks.append(_atomic_split_chunk(tokenizer, block, document_metadata, start_index + len(chunks), header + current_rows))
    return chunks


def _atomic_split_chunk(
    tokenizer: Tokenizer,
    block: dict[str, Any],
    document_metadata: dict[str, Any],
    index: int,
    lines: list[str],
) -> dict[str, Any]:
    split_block = {**block, "id": f"{block.get('id')}-part-{index}", "text": "\n".join(lines)}
    chunk = _chunk_from_blocks(tokenizer, [split_block], document_metadata, index)
    chunk["chunk_metadata"]["split_from_block_id"] = block.get("id")
    return chunk


def citation_fields_from_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical citation shape used by all retrieval modes."""
    fields = {
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "section_path": chunk.get("section_path"),
        "chunk_type": chunk.get("chunk_type"),
        "artifact_manifest_path": chunk.get("artifact_manifest_path"),
        "chunk_metadata": chunk.get("chunk_metadata"),
    }
    return {key: value for key, value in fields.items() if value not in (None, "", {})}


def _is_table_row(line: str) -> bool:
    return line.startswith("|") and line.endswith("|") and line.count("|") >= 2


def _collect_artifact_refs(blocks: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for block in blocks:
        for ref in block.get("artifact_refs") or []:
            if ref not in refs:
                refs.append(ref)
    return refs


def _collect_docling_refs(blocks: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for block in blocks:
        for ref in block.get("docling_refs") or []:
            if ref and ref not in refs:
                refs.append(ref)
    return refs


def _collect_unique(values) -> list[Any]:
    result = []
    for value in values:
        if value not in (None, "", []) and value not in result:
            result.append(value)
    return result


def _flatten_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened = []
    for section in sections or []:
        flattened.append(section)
        flattened.extend(_flatten_sections(section.get("nodes") or []))
    return flattened


def _page_count(blocks: list[dict[str, Any]]) -> int | None:
    pages = {
        page
        for block in blocks
        for page in (block.get("page_start"), block.get("page_end"))
        if page is not None
    }
    return len(pages) or None


def _first_present(values):
    for value in values:
        if value is not None:
            return value
    return None


def _last_present(values):
    found = None
    for value in values:
        if value is not None:
            found = value
    return found


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(k): _json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_json_safe(v) for v in value]
        return str(value)
