from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DOCUMENT_GRAPH_VERSION = "document-graph-v1"


def build_document_graph(document_metadata: dict[str, Any]) -> dict[str, Any]:
    """Build a lightweight navigation graph from structural metadata or manifest JSON."""
    structure = document_metadata.get("structure") or document_metadata
    blocks = [block for block in structure.get("blocks") or [] if block.get("chunkable", True)]
    sections = structure.get("sections") or []
    manifest_path = (
        document_metadata.get("artifact_manifest_path")
        or document_metadata.get("manifest_path")
        or ""
    )
    doc_id = document_metadata.get("doc_id") or manifest_path or "unknown"

    graph: dict[str, Any] = {
        "version": DOCUMENT_GRAPH_VERSION,
        "doc_id": doc_id,
        "artifact_manifest_path": manifest_path,
        "nodes": {},
        "edges": [],
        "block_order": [],
        "section_order": [],
        "structural_node_order": [],
        "section_children": {},
    }

    doc_node_id = _document_node_id(doc_id)
    graph["nodes"][doc_node_id] = {
        "id": doc_node_id,
        "kind": "document",
        "doc_id": doc_id,
        "artifact_manifest_path": manifest_path,
    }

    section_paths = _section_paths(sections)
    for section in _flatten_sections(sections):
        section_id = _section_node_id(section)
        parent_id = _section_parent_id(section, section_paths) or doc_node_id
        node = _section_graph_node(section, section_paths.get(str(section.get("node_id")), []))
        graph["nodes"][section_id] = node
        graph["section_order"].append(section_id)
        graph["edges"].append(_edge(parent_id, section_id, "HAS_SECTION"))
        graph["section_children"].setdefault(parent_id, []).append(section_id)

    _add_section_sequence_edges(graph, sections)

    for index, block in enumerate(blocks):
        block_id = str(block.get("id") or f"block-{index:05d}")
        node = _block_graph_node(block, manifest_path)
        graph["nodes"][block_id] = node
        graph["block_order"].append(block_id)
        if node.get("navigation_kind") == "structure":
            graph["structural_node_order"].append(block_id)

        section_id = block.get("section_node_id")
        parent_id = f"section:{section_id}" if section_id else doc_node_id
        if parent_id not in graph["nodes"]:
            parent_id = doc_node_id
        graph["edges"].append(_edge(parent_id, block_id, "CONTAINS_BLOCK"))
        graph["section_children"].setdefault(parent_id, []).append(block_id)

    for previous_id, next_id in zip(graph["block_order"], graph["block_order"][1:]):
        previous = graph["nodes"].get(previous_id, {})
        current = graph["nodes"].get(next_id, {})
        if previous.get("section_node_id") == current.get("section_node_id"):
            graph["edges"].append(_edge(previous_id, next_id, "NEXT_BLOCK"))

    return graph


def expand_navigation_context(
    document_metadata: dict[str, Any],
    *,
    center_block_ids: list[str],
    window: int = 1,
    include_parent_section: bool = True,
) -> dict[str, Any]:
    """Return a bounded previous/current/next navigation window around block ids."""
    graph = build_document_graph(document_metadata)
    block_order = graph.get("block_order") or []
    block_positions = {block_id: index for index, block_id in enumerate(block_order)}
    normalized_centers = [block_id for block_id in center_block_ids if block_id in block_positions]
    bounded_window = max(0, min(int(window), 3))

    previous: list[dict[str, Any]] = []
    center: list[dict[str, Any]] = []
    next_blocks: list[dict[str, Any]] = []
    parent_sections: list[dict[str, Any]] = []
    seen_sections: set[str] = set()
    center_set = set(normalized_centers)

    for block_id in normalized_centers:
        position = block_positions[block_id]
        center.append(_context_node(graph, block_id, "center"))

        for neighbor_id in block_order[max(0, position - bounded_window) : position]:
            if neighbor_id not in center_set and _same_section(graph, block_id, neighbor_id):
                previous.append(_context_node(graph, neighbor_id, "previous_block"))

        for neighbor_id in block_order[position + 1 : position + 1 + bounded_window]:
            if neighbor_id not in center_set and _same_section(graph, block_id, neighbor_id):
                next_blocks.append(_context_node(graph, neighbor_id, "next_block"))

        section_node_id = graph["nodes"][block_id].get("section_node_id")
        if include_parent_section and section_node_id:
            section_id = f"section:{section_node_id}"
            if section_id in graph["nodes"] and section_id not in seen_sections:
                parent_sections.append(_context_node(graph, section_id, "parent_section"))
                seen_sections.add(section_id)

    return {
        "navigation_meta": {
            "version": DOCUMENT_GRAPH_VERSION,
            "window": bounded_window,
            "requested_block_ids": center_block_ids,
            "resolved_block_ids": normalized_centers,
            "artifact_manifest_path": graph.get("artifact_manifest_path"),
        },
        "parent_sections": parent_sections,
        "previous_blocks": _dedupe_context_nodes(previous),
        "center_blocks": _dedupe_context_nodes(center),
        "next_blocks": _dedupe_context_nodes(next_blocks),
    }


def load_structural_manifest(working_dir: str | Path, artifact_manifest_path: str) -> dict[str, Any]:
    """Load a structural artifact manifest using this repo's domain-relative convention."""
    manifest_path = Path(artifact_manifest_path)
    if not manifest_path.is_absolute():
        base = Path(working_dir).resolve()
        if base.name == "rag_storage":
            base = base.parent
        manifest_path = base / manifest_path
    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)
    manifest.setdefault("artifact_manifest_path", artifact_manifest_path)
    return manifest


def _document_node_id(doc_id: Any) -> str:
    return f"document:{doc_id}"


def _section_node_id(section: dict[str, Any]) -> str:
    return f"section:{section.get('node_id')}"


def _section_parent_id(
    section: dict[str, Any], section_paths: dict[str, list[dict[str, Any]]]
) -> str | None:
    path = section_paths.get(section.get("node_id"), [])
    if len(path) < 2:
        return None
    return _section_node_id(path[-2])


def _section_graph_node(section: dict[str, Any], path: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": _section_node_id(section),
        "kind": "section",
        "section_node_id": section.get("node_id"),
        "title": section.get("title"),
        "section_path": " > ".join(str(item.get("title") or "") for item in path if item.get("title")),
        "page_start": section.get("page_start"),
        "page_end": section.get("page_end"),
        "block_ids": [str(value) for value in section.get("block_ids") or []],
        "docling_refs": [str(value) for value in section.get("docling_refs") or []],
    }


def _block_graph_node(block: dict[str, Any], manifest_path: str) -> dict[str, Any]:
    navigation_kind = block.get("navigation_kind") or (
        "structure" if _is_structural_block(block) else "prose"
    )
    return {
        "id": str(block.get("id")),
        "kind": "structure" if navigation_kind == "structure" else "block",
        "navigation_kind": navigation_kind,
        "block_type": block.get("type"),
        "label": block.get("label"),
        "structural_role": block.get("structural_role"),
        "kg_extractable": block.get("kg_extractable"),
        "text": block.get("text") or "",
        "page_start": block.get("page_start"),
        "page_end": block.get("page_end"),
        "section_path": " > ".join(block.get("section_path") or []),
        "section_node_id": block.get("section_node_id"),
        "docling_refs": [str(value) for value in block.get("docling_refs") or []],
        "artifact_refs": [str(value) for value in block.get("artifact_refs") or []],
        "artifact_manifest_path": manifest_path,
    }


def _edge(src_id: str, tgt_id: str, edge_type: str) -> dict[str, str]:
    return {"src_id": src_id, "tgt_id": tgt_id, "edge_type": edge_type}


def _add_section_sequence_edges(graph: dict[str, Any], sections: list[dict[str, Any]]) -> None:
    for siblings in _section_sibling_groups(sections):
        for previous, current in zip(siblings, siblings[1:]):
            previous_id = _section_node_id(previous)
            current_id = _section_node_id(current)
            graph["edges"].append(_edge(previous_id, current_id, "NEXT_SECTION"))
            graph["edges"].append(_edge(current_id, previous_id, "PREVIOUS_SECTION"))


def _section_sibling_groups(sections: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []

    def visit(nodes: list[dict[str, Any]]) -> None:
        if len(nodes) > 1:
            groups.append(nodes)
        for node in nodes:
            visit(node.get("nodes") or [])

    visit(sections or [])
    return groups


def _flatten_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened = []
    for section in sections or []:
        flattened.append(section)
        flattened.extend(_flatten_sections(section.get("nodes") or []))
    return flattened


def _section_paths(sections: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    paths: dict[str, list[dict[str, Any]]] = {}

    def visit(nodes: list[dict[str, Any]], trail: list[dict[str, Any]]) -> None:
        for node in nodes or []:
            node_id = node.get("node_id")
            next_trail = trail + [node]
            if node_id:
                paths[str(node_id)] = next_trail
            visit(node.get("nodes") or [], next_trail)

    visit(sections, [])
    return paths


def _same_section(graph: dict[str, Any], first_id: str, second_id: str) -> bool:
    first = graph["nodes"].get(first_id, {})
    second = graph["nodes"].get(second_id, {})
    return first.get("section_node_id") == second.get("section_node_id")


def _is_structural_block(block: dict[str, Any]) -> bool:
    role = block.get("structural_role")
    if role and role != "prose":
        return True
    block_type = block.get("type")
    label = block.get("label")
    if block_type in {"table", "figure", "caption", "code", "heading", "layout"}:
        return True
    return label in {"document_index", "caption", "picture", "page_header", "page_footer"}


def _context_node(graph: dict[str, Any], node_id: str, reason: str) -> dict[str, Any]:
    node = dict(graph["nodes"][node_id])
    node["reason"] = reason
    return node


def _dedupe_context_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for node in nodes:
        node_id = str(node.get("id"))
        if node_id in seen:
            continue
        seen.add(node_id)
        deduped.append(node)
    return deduped
