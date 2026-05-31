from __future__ import annotations
from functools import partial

import asyncio
import json
import re
import os
from typing import Any, AsyncIterator
from collections import Counter, defaultdict

from .utils import (
    logger,
    clean_str,
    compute_mdhash_id,
    Tokenizer,
    is_float_regex,
    normalize_extracted_info,
    pack_user_ass_to_openai_messages,
    split_string_by_multi_markers,
    truncate_list_by_token_size,
    process_combine_contexts,
    compute_args_hash,
    handle_cache,
    save_to_cache,
    CacheData,
    get_conversation_turns,
    use_llm_func_with_cache,
    update_chunk_cache_list,
    remove_think_tags,
)
from .base import (
    BaseGraphStorage,
    BaseKVStorage,
    BaseVectorStorage,
    TextChunkSchema,
    QueryParam,
)
from .document_graph import expand_navigation_context, load_structural_manifest
from .structural_chunking import citation_fields_from_chunk
from .prompt import PROMPTS
from .constants import GRAPH_FIELD_SEP
from .kg.shared_storage import get_graph_db_lock_keyed
import time
from dotenv import load_dotenv

# use the .env that is inside the current folder
# allows to use different .env file for each lightrag instance
# the OS environment variables take precedence over the .env file
load_dotenv(dotenv_path=".env", override=False)


# CUSTOM: Token chunking defaults and parameter names (max_token_size / overlap_token_size)
# aligned with this deployment; split_by_character_only no longer raises on oversized chunks
# (upstream used ChunkTokenLimitExceededError there).
def chunking_by_token_size(
    tokenizer: Tokenizer,
    content: str,
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
    overlap_token_size: int = 128,
    max_token_size: int = 1024,
) -> list[dict[str, Any]]:
    tokens = tokenizer.encode(content)
    results: list[dict[str, Any]] = []
    if split_by_character:
        raw_chunks = content.split(split_by_character)
        new_chunks = []
        if split_by_character_only:
            for chunk in raw_chunks:
                _tokens = tokenizer.encode(chunk)
                new_chunks.append((len(_tokens), chunk))
        else:
            for chunk in raw_chunks:
                _tokens = tokenizer.encode(chunk)
                if len(_tokens) > max_token_size:
                    for start in range(
                        0, len(_tokens), max_token_size - overlap_token_size
                    ):
                        chunk_content = tokenizer.decode(
                            _tokens[start : start + max_token_size]
                        )
                        new_chunks.append(
                            (min(max_token_size, len(_tokens) - start), chunk_content)
                        )
                else:
                    new_chunks.append((len(_tokens), chunk))
        for index, (_len, chunk) in enumerate(new_chunks):
            results.append(
                {
                    "tokens": _len,
                    "content": chunk.strip(),
                    "chunk_order_index": index,
                }
            )
    else:
        for index, start in enumerate(
            range(0, len(tokens), max_token_size - overlap_token_size)
        ):
            chunk_content = tokenizer.decode(tokens[start : start + max_token_size])
            results.append(
                {
                    "tokens": min(max_token_size, len(tokens) - start),
                    "content": chunk_content.strip(),
                    "chunk_order_index": index,
                }
            )
    return results


# CUSTOM — Structural chunking & retrieval helpers (not in upstream operate.py):
# - Corpus-derived ontology hints and section anchor constants for extraction prompts.
# - JSON-shaped retrieval payloads (_build/_format_retrieval_context, naive variant) for APIs/UI.
# - Chunk id normalization, citation-aware context dicts, structural provenance extraction,
#   embedding text enrichment, synthetic section nodes/edges for the KG, and ontology signal parsing.
_ONTOLOGY_SIGNAL_STOPWORDS = {
    "abstract",
    "appendix",
    "background",
    "chapter",
    "conclusion",
    "contents",
    "definition",
    "definitions",
    "example",
    "examples",
    "figure",
    "introduction",
    "note",
    "overview",
    "references",
    "section",
    "summary",
    "table",
}

SECTION_NODE_PREFIX = "Section: "
SECTION_ENTITY_TYPE = "section"
SECTION_PROVENANCE_KEYWORDS = "document structure, section provenance"
SECTION_HIERARCHY_KEYWORDS = "document structure, section hierarchy"
SECTION_PROVENANCE_WEIGHT = 0.2
SECTION_HIERARCHY_WEIGHT = 0.3


def _chunk_id_from_result(chunk: dict[str, Any]) -> str | None:
    """Return the stable storage id from any supported chunk result shape."""
    for key in ("chunk_id", "id", "__id__"):
        value = chunk.get(key)
        if value:
            return str(value)
    return None


def _chunk_metadata_dict(chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = chunk.get("chunk_metadata")
    return metadata if isinstance(metadata, dict) else {}


def _compact_citation_label(item: Any) -> str:
    """Return document > section, page citation text from existing provenance."""
    source = _source_label(item)
    section = _section_label(item)
    page = _page_label(item)

    label = source
    if section:
        label = f"{label} > {section}"
    if page:
        label = f"{label}, {page}"
    return label


def _source_label(item: Any) -> str:
    if not isinstance(item, dict):
        return "unknown_source"
    for key in ("file_path", "full_doc_id", "chunk_id", "id"):
        value = item.get(key)
        if value not in (None, "", "unknown_source"):
            return str(value).replace("\\", "/").rstrip("/").split("/")[-1]
    return "unknown_source"


def _section_label(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    value = item.get("section_path")
    if not value:
        section_paths = item.get("section_paths")
        if isinstance(section_paths, list) and section_paths:
            value = section_paths[0]
    if isinstance(value, list):
        parts = [str(part).strip() for part in value if str(part).strip()]
    else:
        parts = [part.strip() for part in str(value or "").split(">") if part.strip()]
    return " > ".join(parts) or None


def _page_label(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    page_start = item.get("page_start")
    page_end = item.get("page_end")
    if page_start is None:
        return None
    if page_end is not None and page_end != page_start:
        return f"p.{page_start}-{page_end}"
    return f"p.{page_start}"


def _citation_key(item: dict[str, Any]) -> tuple[str, str, Any, Any]:
    return (
        _source_label(item),
        _section_label(item) or "",
        item.get("page_start"),
        item.get("page_end"),
    )


def _reference_sources(
    entities: list[dict],
    relationships: list[dict],
    chunks: list[dict],
) -> list[dict[str, str]]:
    references: list[dict[str, str]] = []
    seen: set[tuple[str, str, Any, Any]] = set()
    for source_type, items in (
        ("KG", entities),
        ("KG", relationships),
        ("DC", chunks),
    ):
        for item in items:
            if not isinstance(item, dict):
                continue
            key = _citation_key(item)
            if key in seen:
                continue
            seen.add(key)
            citation = item.get("citation_label") or _compact_citation_label(item)
            references.append(
                {
                    "source_type": source_type,
                    "citation": citation,
                    "label": f"[{source_type}] {citation}",
                }
            )
    return references


def _build_chunk_context(chunk: dict[str, Any], ordinal: int) -> dict[str, Any]:
    chunk_context = {
        "id": ordinal,
        "content": chunk["content"],
        "file_path": chunk.get("file_path", "unknown_source"),
        **citation_fields_from_chunk(chunk),
    }
    if not isinstance(chunk_context.get("chunk_metadata"), dict):
        chunk_context.pop("chunk_metadata", None)
    chunk_id = _chunk_id_from_result(chunk)
    if chunk_id:
        chunk_context["chunk_id"] = chunk_id
    for field in (
        "full_doc_id",
        "source_type",
        "distance",
        "created_at",
        "tokens",
        "chunk_order_index",
        "navigation_context",
    ):
        value = chunk.get(field)
        if value is not None:
            chunk_context[field] = value
    chunk_context["citation_label"] = _compact_citation_label(chunk_context)
    return chunk_context


def _build_retrieval_context(
    *,
    query: str,
    mode: str,
    entities: list[dict],
    relationships: list[dict],
    chunks: list[dict],
) -> dict[str, Any]:
    return {
        "query": query,
        "mode": mode,
        "entities": entities,
        "relationships": relationships,
        "chunks": chunks,
        "references": _reference_sources(entities, relationships, chunks),
        "retrieval_meta": {
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "chunk_count": len(chunks),
        },
    }


def _attach_parent_context_to_chunks(
    chunks: list[dict],
    *,
    query_param: QueryParam,
    global_config: dict[str, Any],
) -> tuple[list[dict], dict[str, Any]]:
    """Attach small-to-big navigation context to retrieved structural chunks.

    This keeps retrieval small and precise while giving answer generation the
    parent section plus bounded neighboring blocks when a manifest is available.
    """
    meta = {
        "parent_context_enabled": bool(query_param.enable_parent_context),
        "parent_context_window": max(0, min(int(query_param.parent_context_window), 3)),
        "parent_context_expanded_count": 0,
        "parent_context_error_count": 0,
    }
    if not query_param.enable_parent_context or not chunks:
        return chunks, meta

    working_dir = global_config.get("working_dir")
    if not working_dir:
        meta["parent_context_enabled"] = False
        meta["parent_context_reason"] = "missing working_dir"
        return chunks, meta

    manifest_cache: dict[str, dict[str, Any]] = {}
    expanded_chunks: list[dict] = []
    for chunk in chunks:
        expanded_chunk = dict(chunk)
        chunk_metadata = _chunk_metadata_dict(chunk)
        block_ids = [str(value) for value in chunk_metadata.get("block_ids") or [] if value]
        artifact_manifest_path = chunk.get("artifact_manifest_path")
        if not block_ids or not artifact_manifest_path:
            expanded_chunks.append(expanded_chunk)
            continue

        try:
            manifest = manifest_cache.get(artifact_manifest_path)
            if manifest is None:
                manifest = load_structural_manifest(working_dir, artifact_manifest_path)
                manifest_cache[artifact_manifest_path] = manifest
            expanded_chunk["navigation_context"] = expand_navigation_context(
                manifest,
                center_block_ids=block_ids,
                window=meta["parent_context_window"],
                include_parent_section=query_param.include_parent_section,
            )
            meta["parent_context_expanded_count"] += 1
        except Exception as exc:
            meta["parent_context_error_count"] += 1
            logger.warning(
                "Parent context expansion skipped for chunk %s: %s",
                chunk.get("chunk_id") or chunk.get("id"),
                exc,
            )
        expanded_chunks.append(expanded_chunk)

    return expanded_chunks, meta


def _format_retrieval_context(context: dict[str, Any]) -> str:
    entities_str = json.dumps(context["entities"], ensure_ascii=False)
    relations_str = json.dumps(context["relationships"], ensure_ascii=False)
    text_units_str = json.dumps(context["chunks"], ensure_ascii=False)
    references_str = json.dumps(context.get("references", []), ensure_ascii=False)

    return f"""-----Entities(KG)-----

```json
{entities_str}
```

-----Relationships(KG)-----

```json
{relations_str}
```

-----Document Chunks(DC)-----

```json
{text_units_str}
```

-----Reference Sources-----

```json
{references_str}
```

"""


def _format_naive_context(context: dict[str, Any]) -> str:
    text_units_str = json.dumps(context["chunks"], ensure_ascii=False)
    references_str = json.dumps(context.get("references", []), ensure_ascii=False)
    return f"""
---Document Chunks---

```json
{text_units_str}
```

---Reference Sources---

```json
{references_str}
```

"""


def _build_section_context(chunk: TextChunkSchema) -> str:
    """Format structural chunk metadata as prompt context."""
    fields = []
    section_path = chunk.get("section_path")
    if section_path:
        fields.append(f"Section Path: {section_path}")

    chunk_type = chunk.get("chunk_type")
    if chunk_type:
        fields.append(f"Chunk Type: {chunk_type}")

    page_start = chunk.get("page_start")
    page_end = chunk.get("page_end")
    if page_start is not None and page_end is not None:
        fields.append(f"Pages: {page_start}-{page_end}")
    elif page_start is not None:
        fields.append(f"Page: {page_start}")

    if not fields:
        return "No structural metadata is available for this chunk; use the text content only."
    return "\n".join(fields)


def _chunk_structural_provenance(chunk: dict[str, Any]) -> dict[str, Any]:
    chunk_metadata = _chunk_metadata_dict(chunk)
    section_node_ids = chunk_metadata.get("section_node_ids") or []
    section_node_id = chunk_metadata.get("section_node_id")
    if section_node_id and section_node_id not in section_node_ids:
        section_node_ids = [section_node_id] + list(section_node_ids)
    return {
        "section_path": chunk.get("section_path"),
        "section_node_ids": [str(value) for value in section_node_ids if value],
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "docling_refs": [str(value) for value in chunk_metadata.get("docling_refs") or []],
        "block_ids": [str(value) for value in chunk_metadata.get("block_ids") or []],
        "artifact_manifest_path": chunk.get("artifact_manifest_path"),
    }


def _merge_structural_values(records: list[dict], key: str) -> list[str]:
    values: list[str] = []
    for record in records:
        value = record.get(key)
        if isinstance(value, list):
            candidates = value
        elif value in (None, ""):
            candidates = []
        else:
            candidates = [value]
        for candidate in candidates:
            text = str(candidate)
            if text not in values:
                values.append(text)
    return values


def _merge_page_value(records: list[dict], key: str, reducer) -> int | None:
    values = [record.get(key) for record in records if record.get(key) is not None]
    return reducer(values) if values else None


def _embedding_context_lines(data: dict[str, Any]) -> list[str]:
    lines = []
    if data.get("entity_type"):
        lines.append(f"Type: {data['entity_type']}")
    if data.get("section_paths"):
        lines.append(f"Sections: {', '.join(data['section_paths'])}")
    elif data.get("section_path"):
        lines.append(f"Section: {data['section_path']}")
    page_start = data.get("page_start")
    page_end = data.get("page_end")
    if page_start is not None and page_end is not None:
        lines.append(f"Pages: {page_start}-{page_end}")
    elif page_start is not None:
        lines.append(f"Page: {page_start}")
    return lines


def _is_kg_extractable_chunk(chunk: dict[str, Any]) -> bool:
    chunk_metadata = _chunk_metadata_dict(chunk)
    value = chunk.get("kg_extractable", chunk_metadata.get("kg_extractable", True))
    return value is not False


def _kg_extractable_chunk_items(
    chunks: list[tuple[str, TextChunkSchema]],
) -> list[tuple[str, TextChunkSchema]]:
    return [(chunk_id, chunk) for chunk_id, chunk in chunks if _is_kg_extractable_chunk(chunk)]


def _entity_embedding_content(entity_data: dict[str, Any]) -> str:
    parts = [
        entity_data["entity_name"],
        *_embedding_context_lines(entity_data),
        entity_data["description"],
    ]
    return "\n".join(part for part in parts if part)


def _relationship_embedding_content(edge_data: dict[str, Any]) -> str:
    parts = [
        f"{edge_data['src_id']}\t{edge_data['tgt_id']}",
        edge_data.get("keywords", ""),
        *_embedding_context_lines(edge_data),
        edge_data.get("description", ""),
    ]
    return "\n".join(part for part in parts if part)


def _section_node_name(section_path: str) -> str:
    return f"{SECTION_NODE_PREFIX}{section_path}"


def _section_node_description(section_path: str) -> str:
    return (
        f"Document section anchor for '{section_path}'. This node is generated "
        "from structural document metadata and is used for provenance-aware graph traversal."
    )


def _section_paths_from_path(section_path: str) -> list[str]:
    parts = [
        _normalize_ontology_signal(part)
        for part in section_path.split(">")
    ]
    parts = [part for part in parts if part]
    return [" > ".join(parts[: index + 1]) for index in range(len(parts))]


def _section_node_record(
    section_path: str,
    source_id: str,
    file_path: str,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provenance = provenance or {}
    return {
        "entity_name": _section_node_name(section_path),
        "entity_type": SECTION_ENTITY_TYPE,
        "description": _section_node_description(section_path),
        "source_id": source_id,
        "file_path": file_path,
        "section_path": section_path,
        "section_node_ids": provenance.get("section_node_ids", []),
        "docling_refs": provenance.get("docling_refs", []),
        "block_ids": provenance.get("block_ids", []),
        "artifact_manifest_path": provenance.get("artifact_manifest_path"),
        "page_start": provenance.get("page_start"),
        "page_end": provenance.get("page_end"),
    }


def _section_provenance_edge(
    entity_name: str,
    section_path: str,
    source_id: str,
    file_path: str,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provenance = provenance or {}
    section_node = _section_node_name(section_path)
    return {
        "src_id": entity_name,
        "tgt_id": section_node,
        "weight": SECTION_PROVENANCE_WEIGHT,
        "description": (
            f"{entity_name} appears in document section '{section_path}'. "
            "This relationship is derived from structural metadata, not inferred technical causality."
        ),
        "keywords": SECTION_PROVENANCE_KEYWORDS,
        "source_id": source_id,
        "file_path": file_path,
        "section_path": section_path,
        "section_node_ids": provenance.get("section_node_ids", []),
        "docling_refs": provenance.get("docling_refs", []),
        "block_ids": provenance.get("block_ids", []),
        "artifact_manifest_path": provenance.get("artifact_manifest_path"),
        "page_start": provenance.get("page_start"),
        "page_end": provenance.get("page_end"),
    }


def _section_hierarchy_edge(
    child_section_path: str,
    parent_section_path: str,
    source_id: str,
    file_path: str,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provenance = provenance or {}
    child_section = _section_node_name(child_section_path)
    parent_section = _section_node_name(parent_section_path)
    return {
        "src_id": child_section,
        "tgt_id": parent_section,
        "weight": SECTION_HIERARCHY_WEIGHT,
        "description": (
            f"Document section '{child_section_path}' is nested under "
            f"'{parent_section_path}'. This relationship is derived from structural metadata."
        ),
        "keywords": SECTION_HIERARCHY_KEYWORDS,
        "source_id": source_id,
        "file_path": file_path,
        "section_path": child_section_path,
        "section_node_ids": provenance.get("section_node_ids", []),
        "docling_refs": provenance.get("docling_refs", []),
        "block_ids": provenance.get("block_ids", []),
        "artifact_manifest_path": provenance.get("artifact_manifest_path"),
        "page_start": provenance.get("page_start"),
        "page_end": provenance.get("page_end"),
    }


def _add_section_anchor_nodes_and_edges(
    all_nodes: defaultdict[str, list[dict]],
    all_edges: defaultdict[tuple[str, str], list[dict]],
) -> None:
    hierarchy_edges_seen: set[tuple[str, str, str]] = set()

    for entity_name, entities in list(all_nodes.items()):
        if entity_name.startswith(SECTION_NODE_PREFIX):
            continue

        for entity in entities:
            section_path = entity.get("section_path")
            if not section_path:
                continue

            section_paths = _section_paths_from_path(section_path)
            if not section_paths:
                continue

            source_id = entity.get("source_id", "")
            file_path = entity.get("file_path", "unknown_source")
            provenance = {
                "section_node_ids": entity.get("section_node_ids", []),
                "docling_refs": entity.get("docling_refs", []),
                "block_ids": entity.get("block_ids", []),
                "artifact_manifest_path": entity.get("artifact_manifest_path"),
                "page_start": entity.get("page_start"),
                "page_end": entity.get("page_end"),
            }

            for path in section_paths:
                section_node = _section_node_name(path)
                all_nodes[section_node].append(
                    _section_node_record(path, source_id, file_path, provenance)
                )

            full_section_path = section_paths[-1]
            provenance_edge = _section_provenance_edge(
                entity_name, full_section_path, source_id, file_path, provenance
            )
            all_edges[tuple(sorted((entity_name, provenance_edge["tgt_id"])))].append(
                provenance_edge
            )

            for index in range(1, len(section_paths)):
                child_path = section_paths[index]
                parent_path = section_paths[index - 1]
                seen_key = (child_path, parent_path, source_id)
                if seen_key in hierarchy_edges_seen:
                    continue
                hierarchy_edges_seen.add(seen_key)

                hierarchy_edge = _section_hierarchy_edge(
                    child_path, parent_path, source_id, file_path, provenance
                )
                all_edges[
                    tuple(sorted((hierarchy_edge["src_id"], hierarchy_edge["tgt_id"])))
                ].append(hierarchy_edge)


def _build_corpus_ontology_guidance(
    ordered_chunks: list[tuple[str, TextChunkSchema]],
    max_items: int = 18,
) -> str:
    """Build lightweight domain guidance from the document's structural chunks.

    The returned terms are subtype/example hints only; extraction still uses the
    fixed upper ontology so entity types remain stable across chunks.
    """
    section_terms: Counter[str] = Counter()
    table_fields: Counter[str] = Counter()
    technical_terms: Counter[str] = Counter()

    for _, chunk in ordered_chunks:
        section_path = chunk.get("section_path") or ""
        for section_part in section_path.split(">"):
            term = _normalize_ontology_signal(section_part)
            if term:
                section_terms[term] += 1

        content = chunk.get("content") or ""
        for field in _extract_table_fields(content):
            table_fields[field] += 1
        for term in _extract_technical_terms(content):
            technical_terms[term] += 1

    sections = _top_counter_items(section_terms, max_items)
    fields = _top_counter_items(table_fields, 10)
    terms = _top_counter_items(technical_terms, max_items)

    if not sections and not fields and not terms:
        return (
            "No reliable corpus-specific ontology signals were found. "
            "Use the upper ontology definitions only."
        )

    guidance = [
        "The following corpus-derived signals are subtype/example hints, not allowed entity_type values."
    ]
    if sections:
        guidance.append(f"Section anchors: {', '.join(sections)}")
    if terms:
        guidance.append(f"Repeated technical terms: {', '.join(terms)}")
    if fields:
        guidance.append(f"Table fields: {', '.join(fields)}")
    return "\n".join(guidance)


def _resolve_ontology_guidance(
    addon_params: dict[str, Any],
    ordered_chunks: list[tuple[str, TextChunkSchema]],
) -> str:
    ontology_guidance = addon_params.get("ontology_guidance")
    if ontology_guidance is not None:
        return ontology_guidance
    return _build_corpus_ontology_guidance(ordered_chunks)


def _extract_table_fields(content: str) -> list[str]:
    fields: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        for cell in cells:
            term = _normalize_ontology_signal(cell)
            if term:
                fields.append(term)
        break
    return fields


def _extract_technical_terms(content: str) -> list[str]:
    terms: list[str] = []
    term_pattern = re.compile(
        r"\b(?:[A-Z]{2,}[A-Za-z0-9_+./-]*|"
        r"[A-Z][A-Za-z0-9_+./-]*(?:\s+(?:[A-Z][A-Za-z0-9_+./-]*|"
        r"[a-z][A-Za-z0-9_+./-]{2,})){1,4})\b"
    )
    for match in term_pattern.finditer(content):
        term = _normalize_ontology_signal(match.group(0))
        if term:
            terms.append(term)
    return terms


def _normalize_ontology_signal(value: str) -> str | None:
    value = re.sub(r"^#+\s*", "", value.strip())
    value = re.sub(r"^\d+(?:\.\d+)*\s*[-.)]?\s*", "", value)
    value = re.sub(r"\s+", " ", value.strip(" `*_\"'"))
    value = value.strip()
    if not value or len(value) < 3 or len(value) > 80:
        return None
    if value.lower() in _ONTOLOGY_SIGNAL_STOPWORDS:
        return None
    if all(char in "-:| " for char in value):
        return None
    return value


def _top_counter_items(counter: Counter[str], limit: int) -> list[str]:
    sorted_items = sorted(
        counter.items(),
        key=lambda entry: (-entry[1], entry[0].lower()),
    )
    return [
        item
        for item, _ in sorted_items[:limit]
    ]


# CUSTOM: Single-shot LLM summary when merged descriptions exceed limits (upstream used a
# larger map-reduce _handle_entity_relation_summary with iterative chunking).
async def _handle_entity_relation_summary(
    entity_or_relation_name: str,
    description: str,
    global_config: dict,
    llm_response_cache: BaseKVStorage | None = None,
) -> str:
    """Handle entity relation summary
    For each entity or relation, input is the combined description of already existing description and new description.
    If too long, use LLM to summarize.
    """
    use_llm_func: callable = global_config["llm_model_func"]
    # Apply higher priority (8) to entity/relation summary tasks
    use_llm_func = partial(use_llm_func, _priority=8)

    tokenizer: Tokenizer = global_config["tokenizer"]
    llm_max_tokens = global_config["llm_model_max_token_size"]
    summary_max_tokens = global_config["summary_to_max_tokens"]

    language = global_config["addon_params"].get(
        "language", PROMPTS["DEFAULT_LANGUAGE"]
    )

    tokens = tokenizer.encode(description)

    ### summarize is not determined here anymore (It's determined by num_fragment now)
    # if len(tokens) < summary_max_tokens:  # No need for summary
    #     return description

    prompt_template = PROMPTS["summarize_entity_descriptions"]
    use_description = tokenizer.decode(tokens[:llm_max_tokens])
    context_base = dict(
        entity_name=entity_or_relation_name,
        description_list=use_description.split(GRAPH_FIELD_SEP),
        language=language,
    )
    use_prompt = prompt_template.format(**context_base)
    logger.debug(f"Trigger summary: {entity_or_relation_name}")

    # Use LLM function with cache (higher priority for summary generation)
    summary = await use_llm_func_with_cache(
        use_prompt,
        use_llm_func,
        llm_response_cache=llm_response_cache,
        max_tokens=summary_max_tokens,
        cache_type="extract",
    )
    return summary


# CUSTOM: Entity extraction record enriched with structural provenance (section_path,
# docling_refs, block_ids, artifact manifest, page span) for citation-aware KG nodes.
async def _handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
    file_path: str = "unknown_source",
    section_path: str | None = None,
    provenance: dict[str, Any] | None = None,
):
    if len(record_attributes) < 4 or '"entity"' not in record_attributes[0]:
        return None

    # Clean and validate entity name
    entity_name = clean_str(record_attributes[1]).strip()
    if not entity_name:
        logger.warning(
            f"Entity extraction error: empty entity name in: {record_attributes}"
        )
        return None

    # Normalize entity name
    entity_name = normalize_extracted_info(entity_name, is_entity=True)

    # Check if entity name became empty after normalization
    if not entity_name or not entity_name.strip():
        logger.warning(
            f"Entity extraction error: entity name became empty after normalization. Original: '{record_attributes[1]}'"
        )
        return None

    # Clean and validate entity type
    entity_type = clean_str(record_attributes[2]).strip('"')
    if not entity_type.strip() or entity_type.startswith('("'):
        logger.warning(
            f"Entity extraction error: invalid entity type in: {record_attributes}"
        )
        return None

    # Clean and validate description
    entity_description = clean_str(record_attributes[3])
    entity_description = normalize_extracted_info(entity_description)

    if not entity_description.strip():
        logger.warning(
            f"Entity extraction error: empty description for entity '{entity_name}' of type '{entity_type}'"
        )
        return None

    provenance = provenance or {}
    return dict(
        entity_name=entity_name,
        entity_type=entity_type,
        description=entity_description,
        source_id=chunk_key,
        file_path=file_path,
        section_path=section_path,
        section_node_ids=provenance.get("section_node_ids", []),
        docling_refs=provenance.get("docling_refs", []),
        block_ids=provenance.get("block_ids", []),
        artifact_manifest_path=provenance.get("artifact_manifest_path"),
        page_start=provenance.get("page_start"),
        page_end=provenance.get("page_end"),
    )


# CUSTOM: Relationship extraction record carries the same structural provenance fields as entities.
async def _handle_single_relationship_extraction(
    record_attributes: list[str],
    chunk_key: str,
    file_path: str = "unknown_source",
    section_path: str | None = None,
    provenance: dict[str, Any] | None = None,
):
    if len(record_attributes) < 5 or '"relationship"' not in record_attributes[0]:
        return None
    # add this record as edge
    source = clean_str(record_attributes[1])
    target = clean_str(record_attributes[2])

    # Normalize source and target entity names
    source = normalize_extracted_info(source, is_entity=True)
    target = normalize_extracted_info(target, is_entity=True)

    # Check if source or target became empty after normalization
    if not source or not source.strip():
        logger.warning(
            f"Relationship extraction error: source entity became empty after normalization. Original: '{record_attributes[1]}'"
        )
        return None

    if not target or not target.strip():
        logger.warning(
            f"Relationship extraction error: target entity became empty after normalization. Original: '{record_attributes[2]}'"
        )
        return None

    if source == target:
        logger.debug(
            f"Relationship source and target are the same in: {record_attributes}"
        )
        return None

    edge_description = clean_str(record_attributes[3])
    edge_description = normalize_extracted_info(edge_description)

    edge_keywords = normalize_extracted_info(
        clean_str(record_attributes[4]), is_entity=True
    )
    edge_keywords = edge_keywords.replace("，", ",")

    edge_source_id = chunk_key
    weight = (
        float(record_attributes[-1].strip('"').strip("'"))
        if is_float_regex(record_attributes[-1].strip('"').strip("'"))
        else 1.0
    )
    provenance = provenance or {}
    return dict(
        src_id=source,
        tgt_id=target,
        weight=weight,
        description=edge_description,
        keywords=edge_keywords,
        source_id=edge_source_id,
        file_path=file_path,
        section_path=section_path,
        section_node_ids=provenance.get("section_node_ids", []),
        docling_refs=provenance.get("docling_refs", []),
        block_ids=provenance.get("block_ids", []),
        artifact_manifest_path=provenance.get("artifact_manifest_path"),
        page_start=provenance.get("page_start"),
        page_end=provenance.get("page_end"),
    )


# CUSTOM: Rebuild entity/relation descriptions from cached LLM extraction outputs after deletes/edits,
# without re-running extraction over chunk text (not present in upstream operate.py).
async def _rebuild_knowledge_from_chunks(
    entities_to_rebuild: dict[str, set[str]],
    relationships_to_rebuild: dict[tuple[str, str], set[str]],
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_storage: BaseKVStorage,
    llm_response_cache: BaseKVStorage,
    global_config: dict[str, str],
    pipeline_status: dict | None = None,
    pipeline_status_lock=None,
) -> None:
    """Rebuild entity and relationship descriptions from cached extraction results

    This method uses cached LLM extraction results instead of calling LLM again,
    following the same approach as the insert process.

    Args:
        entities_to_rebuild: Dict mapping entity_name -> set of remaining chunk_ids
        relationships_to_rebuild: Dict mapping (src, tgt) -> set of remaining chunk_ids
        text_chunks_data: Pre-loaded chunk data dict {chunk_id: chunk_data}
    """
    if not entities_to_rebuild and not relationships_to_rebuild:
        return
    rebuilt_entities_count = 0
    rebuilt_relationships_count = 0

    # Get all referenced chunk IDs
    all_referenced_chunk_ids = set()
    for chunk_ids in entities_to_rebuild.values():
        all_referenced_chunk_ids.update(chunk_ids)
    for chunk_ids in relationships_to_rebuild.values():
        all_referenced_chunk_ids.update(chunk_ids)

    status_message = f"Rebuilding knowledge from {len(all_referenced_chunk_ids)} cached chunk extractions"
    logger.info(status_message)
    if pipeline_status is not None and pipeline_status_lock is not None:
        async with pipeline_status_lock:
            pipeline_status["latest_message"] = status_message
            pipeline_status["history_messages"].append(status_message)

    # Get cached extraction results for these chunks using storage
    #    cached_results： chunk_id -> [list of extraction result from LLM cache sorted by created_at]
    cached_results = await _get_cached_extraction_results(
        llm_response_cache,
        all_referenced_chunk_ids,
        text_chunks_storage=text_chunks_storage,
    )

    if not cached_results:
        status_message = "No cached extraction results found, cannot rebuild"
        logger.warning(status_message)
        if pipeline_status is not None and pipeline_status_lock is not None:
            async with pipeline_status_lock:
                pipeline_status["latest_message"] = status_message
                pipeline_status["history_messages"].append(status_message)
        return

    # Process cached results to get entities and relationships for each chunk
    chunk_entities = {}  # chunk_id -> {entity_name: [entity_data]}
    chunk_relationships = {}  # chunk_id -> {(src, tgt): [relationship_data]}

    for chunk_id, extraction_results in cached_results.items():
        try:
            # Handle multiple extraction results per chunk
            chunk_entities[chunk_id] = defaultdict(list)
            chunk_relationships[chunk_id] = defaultdict(list)

            # process multiple LLM extraction results for a single chunk_id
            for extraction_result in extraction_results:
                entities, relationships = await _parse_extraction_result(
                    text_chunks_storage=text_chunks_storage,
                    extraction_result=extraction_result,
                    chunk_id=chunk_id,
                )

                # Merge entities and relationships from this extraction result
                # Only keep the first occurrence of each entity_name in the same chunk_id
                for entity_name, entity_list in entities.items():
                    if (
                        entity_name not in chunk_entities[chunk_id]
                        or len(chunk_entities[chunk_id][entity_name]) == 0
                    ):
                        chunk_entities[chunk_id][entity_name].extend(entity_list)

                # Only keep the first occurrence of each rel_key in the same chunk_id
                for rel_key, rel_list in relationships.items():
                    if (
                        rel_key not in chunk_relationships[chunk_id]
                        or len(chunk_relationships[chunk_id][rel_key]) == 0
                    ):
                        chunk_relationships[chunk_id][rel_key].extend(rel_list)

        except Exception as e:
            status_message = (
                f"Failed to parse cached extraction result for chunk {chunk_id}: {e}"
            )
            logger.info(status_message)  # Per requirement, change to info
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)
            continue

    # Rebuild entities
    for entity_name, chunk_ids in entities_to_rebuild.items():
        try:
            await _rebuild_single_entity(
                knowledge_graph_inst=knowledge_graph_inst,
                entities_vdb=entities_vdb,
                entity_name=entity_name,
                chunk_ids=chunk_ids,
                chunk_entities=chunk_entities,
                llm_response_cache=llm_response_cache,
                global_config=global_config,
            )
            rebuilt_entities_count += 1
            status_message = (
                f"Rebuilt entity: {entity_name} from {len(chunk_ids)} chunks"
            )
            logger.info(status_message)
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)
        except Exception as e:
            status_message = f"Failed to rebuild entity {entity_name}: {e}"
            logger.info(status_message)  # Per requirement, change to info
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)

    # Rebuild relationships
    for (src, tgt), chunk_ids in relationships_to_rebuild.items():
        try:
            await _rebuild_single_relationship(
                knowledge_graph_inst=knowledge_graph_inst,
                relationships_vdb=relationships_vdb,
                src=src,
                tgt=tgt,
                chunk_ids=chunk_ids,
                chunk_relationships=chunk_relationships,
                llm_response_cache=llm_response_cache,
                global_config=global_config,
            )
            rebuilt_relationships_count += 1
            status_message = (
                f"Rebuilt relationship: {src}->{tgt} from {len(chunk_ids)} chunks"
            )
            logger.info(status_message)
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)
        except Exception as e:
            status_message = f"Failed to rebuild relationship {src}->{tgt}: {e}"
            logger.info(status_message)
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)

    status_message = f"KG rebuild completed: {rebuilt_entities_count} entities and {rebuilt_relationships_count} relationships."
    logger.info(status_message)
    if pipeline_status is not None and pipeline_status_lock is not None:
        async with pipeline_status_lock:
            pipeline_status["latest_message"] = status_message
            pipeline_status["history_messages"].append(status_message)


# CUSTOM: Resolve ordered cached extraction strings per chunk_id via chunk.llm_cache_list + extract cache.
async def _get_cached_extraction_results(
    llm_response_cache: BaseKVStorage,
    chunk_ids: set[str],
    text_chunks_storage: BaseKVStorage,
) -> dict[str, list[str]]:
    """Get cached extraction results for specific chunk IDs

    Args:
        llm_response_cache: LLM response cache storage
        chunk_ids: Set of chunk IDs to get cached results for
        text_chunks_data: Pre-loaded chunk data (optional, for performance)
        text_chunks_storage: Text chunks storage (fallback if text_chunks_data is None)

    Returns:
        Dict mapping chunk_id -> list of extraction_result_text
    """
    cached_results = {}

    # Collect all LLM cache IDs from chunks
    all_cache_ids = set()

    # Read from storage
    chunk_data_list = await text_chunks_storage.get_by_ids(list(chunk_ids))
    for chunk_id, chunk_data in zip(chunk_ids, chunk_data_list):
        if chunk_data and isinstance(chunk_data, dict):
            llm_cache_list = chunk_data.get("llm_cache_list", [])
            if llm_cache_list:
                all_cache_ids.update(llm_cache_list)
        else:
            logger.warning(
                f"Chunk {chunk_id} data is invalid or None: {type(chunk_data)}"
            )

    if not all_cache_ids:
        logger.warning(f"No LLM cache IDs found for {len(chunk_ids)} chunk IDs")
        return cached_results

    # Batch get LLM cache entries
    cache_data_list = await llm_response_cache.get_by_ids(list(all_cache_ids))

    # Process cache entries and group by chunk_id
    valid_entries = 0
    for cache_id, cache_entry in zip(all_cache_ids, cache_data_list):
        if (
            cache_entry is not None
            and isinstance(cache_entry, dict)
            and cache_entry.get("cache_type") == "extract"
            and cache_entry.get("chunk_id") in chunk_ids
        ):
            chunk_id = cache_entry["chunk_id"]
            extraction_result = cache_entry["return"]
            create_time = cache_entry.get(
                "create_time", 0
            )  # Get creation time, default to 0
            valid_entries += 1

            # Support multiple LLM caches per chunk
            if chunk_id not in cached_results:
                cached_results[chunk_id] = []
            # Store tuple with extraction result and creation time for sorting
            cached_results[chunk_id].append((extraction_result, create_time))

    # Sort extraction results by create_time for each chunk
    for chunk_id in cached_results:
        # Sort by create_time (x[1]), then extract only extraction_result (x[0])
        cached_results[chunk_id].sort(key=lambda x: x[1])
        cached_results[chunk_id] = [item[0] for item in cached_results[chunk_id]]

    logger.info(
        f"Found {valid_entries} valid cache entries, {len(cached_results)} chunks with results"
    )
    return cached_results


# CUSTOM: Re-parse cached extraction tuples using the same structural provenance path as live extract_entities.
async def _parse_extraction_result(
    text_chunks_storage: BaseKVStorage, extraction_result: str, chunk_id: str
) -> tuple[dict, dict]:
    """Parse cached extraction result using the same logic as extract_entities

    Args:
        text_chunks_storage: Text chunks storage to get chunk data
        extraction_result: The cached LLM extraction result
        chunk_id: The chunk ID for source tracking

    Returns:
        Tuple of (entities_dict, relationships_dict)
    """

    # Get chunk data for file_path from storage
    chunk_data = await text_chunks_storage.get_by_id(chunk_id)
    file_path = (
        chunk_data.get("file_path", "unknown_source")
        if chunk_data
        else "unknown_source"
    )
    section_path = chunk_data.get("section_path") if chunk_data else None
    provenance = _chunk_structural_provenance(chunk_data or {})
    context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
    )
    maybe_nodes = defaultdict(list)
    maybe_edges = defaultdict(list)

    # Parse the extraction result using the same logic as in extract_entities
    records = split_string_by_multi_markers(
        extraction_result,
        [context_base["record_delimiter"], context_base["completion_delimiter"]],
    )
    for record in records:
        record = re.search(r"\((.*)\)", record)
        if record is None:
            continue
        record = record.group(1)
        record_attributes = split_string_by_multi_markers(
            record, [context_base["tuple_delimiter"]]
        )

        # Try to parse as entity
        entity_data = await _handle_single_entity_extraction(
            record_attributes, chunk_id, file_path, section_path, provenance
        )
        if entity_data is not None:
            maybe_nodes[entity_data["entity_name"]].append(entity_data)
            continue

        # Try to parse as relationship
        relationship_data = await _handle_single_relationship_extraction(
            record_attributes, chunk_id, file_path, section_path, provenance
        )
        if relationship_data is not None:
            maybe_edges[
                (relationship_data["src_id"], relationship_data["tgt_id"])
            ].append(relationship_data)

    return dict(maybe_nodes), dict(maybe_edges)


async def _rebuild_single_entity(
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    entity_name: str,
    chunk_ids: set[str],
    chunk_entities: dict,
    llm_response_cache: BaseKVStorage,
    global_config: dict[str, str],
) -> None:
    """Rebuild a single entity from cached extraction results"""

    # Get current entity data
    current_entity = await knowledge_graph_inst.get_node(entity_name)
    if not current_entity:
        return

    # Helper function to update entity in both graph and vector storage
    async def _update_entity_storage(
        final_description: str, entity_type: str, file_paths: set[str]
    ):
        # Update entity in graph storage
        updated_entity_data = {
            **current_entity,
            "description": final_description,
            "entity_type": entity_type,
            "source_id": GRAPH_FIELD_SEP.join(chunk_ids),
            "file_path": GRAPH_FIELD_SEP.join(file_paths)
            if file_paths
            else current_entity.get("file_path", "unknown_source"),
        }
        await knowledge_graph_inst.upsert_node(entity_name, updated_entity_data)

        # Update entity in vector database
        entity_vdb_id = compute_mdhash_id(entity_name, prefix="ent-")

        # Delete old vector record first
        try:
            await entities_vdb.delete([entity_vdb_id])
        except Exception as e:
            logger.debug(
                f"Could not delete old entity vector record {entity_vdb_id}: {e}"
            )

        # Insert new vector record
        entity_content = f"{entity_name}\n{final_description}"
        await entities_vdb.upsert(
            {
                entity_vdb_id: {
                    "content": entity_content,
                    "entity_name": entity_name,
                    "source_id": updated_entity_data["source_id"],
                    "description": final_description,
                    "entity_type": entity_type,
                    "file_path": updated_entity_data["file_path"],
                }
            }
        )

    # Helper function to generate final description with optional LLM summary
    async def _generate_final_description(combined_description: str) -> str:
        if len(combined_description) > global_config["summary_to_max_tokens"]:
            return await _handle_entity_relation_summary(
                entity_name,
                combined_description,
                global_config,
                llm_response_cache=llm_response_cache,
            )
        else:
            return combined_description

    # Collect all entity data from relevant chunks
    all_entity_data = []
    for chunk_id in chunk_ids:
        if chunk_id in chunk_entities and entity_name in chunk_entities[chunk_id]:
            all_entity_data.extend(chunk_entities[chunk_id][entity_name])

    if not all_entity_data:
        logger.warning(
            f"No cached entity data found for {entity_name}, trying to rebuild from relationships"
        )

        # Get all edges connected to this entity
        edges = await knowledge_graph_inst.get_node_edges(entity_name)
        if not edges:
            logger.warning(f"No relationships found for entity {entity_name}")
            return

        # Collect relationship data to extract entity information
        relationship_descriptions = []
        file_paths = set()

        # Get edge data for all connected relationships
        for src_id, tgt_id in edges:
            edge_data = await knowledge_graph_inst.get_edge(src_id, tgt_id)
            if edge_data:
                if edge_data.get("description"):
                    relationship_descriptions.append(edge_data["description"])

                if edge_data.get("file_path"):
                    edge_file_paths = edge_data["file_path"].split(GRAPH_FIELD_SEP)
                    file_paths.update(edge_file_paths)

        # Generate description from relationships or fallback to current
        if relationship_descriptions:
            combined_description = GRAPH_FIELD_SEP.join(relationship_descriptions)
            final_description = await _generate_final_description(combined_description)
        else:
            final_description = current_entity.get("description", "")

        entity_type = current_entity.get("entity_type", "UNKNOWN")
        await _update_entity_storage(final_description, entity_type, file_paths)
        return

    # Process cached entity data
    descriptions = []
    entity_types = []
    file_paths = set()

    for entity_data in all_entity_data:
        if entity_data.get("description"):
            descriptions.append(entity_data["description"])
        if entity_data.get("entity_type"):
            entity_types.append(entity_data["entity_type"])
        if entity_data.get("file_path"):
            file_paths.add(entity_data["file_path"])

    # Combine all descriptions
    combined_description = (
        GRAPH_FIELD_SEP.join(descriptions)
        if descriptions
        else current_entity.get("description", "")
    )

    # Get most common entity type
    entity_type = (
        max(set(entity_types), key=entity_types.count)
        if entity_types
        else current_entity.get("entity_type", "UNKNOWN")
    )

    # Generate final description and update storage
    final_description = await _generate_final_description(combined_description)
    await _update_entity_storage(final_description, entity_type, file_paths)


async def _rebuild_single_relationship(
    knowledge_graph_inst: BaseGraphStorage,
    relationships_vdb: BaseVectorStorage,
    src: str,
    tgt: str,
    chunk_ids: set[str],
    chunk_relationships: dict,
    llm_response_cache: BaseKVStorage,
    global_config: dict[str, str],
) -> None:
    """Rebuild a single relationship from cached extraction results"""

    # Get current relationship data
    current_relationship = await knowledge_graph_inst.get_edge(src, tgt)
    if not current_relationship:
        return

    # Collect all relationship data from relevant chunks
    all_relationship_data = []
    for chunk_id in chunk_ids:
        if chunk_id in chunk_relationships:
            # Check both (src, tgt) and (tgt, src) since relationships can be bidirectional
            for edge_key in [(src, tgt), (tgt, src)]:
                if edge_key in chunk_relationships[chunk_id]:
                    all_relationship_data.extend(
                        chunk_relationships[chunk_id][edge_key]
                    )

    if not all_relationship_data:
        logger.warning(f"No cached relationship data found for {src}-{tgt}")
        return

    # Merge descriptions and keywords
    descriptions = []
    keywords = []
    weights = []
    file_paths = set()

    for rel_data in all_relationship_data:
        if rel_data.get("description"):
            descriptions.append(rel_data["description"])
        if rel_data.get("keywords"):
            keywords.append(rel_data["keywords"])
        if rel_data.get("weight"):
            weights.append(rel_data["weight"])
        if rel_data.get("file_path"):
            file_paths.add(rel_data["file_path"])

    # Combine descriptions and keywords
    combined_description = (
        GRAPH_FIELD_SEP.join(descriptions)
        if descriptions
        else current_relationship.get("description", "")
    )
    combined_keywords = (
        ", ".join(set(keywords))
        if keywords
        else current_relationship.get("keywords", "")
    )
    # weight = (
    #     sum(weights) / len(weights)
    #     if weights
    #     else current_relationship.get("weight", 1.0)
    # )
    weight = sum(weights) if weights else current_relationship.get("weight", 1.0)

    # Use summary if description is too long
    if len(combined_description) > global_config["summary_to_max_tokens"]:
        final_description = await _handle_entity_relation_summary(
            f"{src}-{tgt}",
            combined_description,
            global_config,
            llm_response_cache=llm_response_cache,
        )
    else:
        final_description = combined_description

    # Update relationship in graph storage
    updated_relationship_data = {
        **current_relationship,
        "description": final_description,
        "keywords": combined_keywords,
        "weight": weight,
        "source_id": GRAPH_FIELD_SEP.join(chunk_ids),
        "file_path": GRAPH_FIELD_SEP.join(file_paths)
        if file_paths
        else current_relationship.get("file_path", "unknown_source"),
    }
    await knowledge_graph_inst.upsert_edge(src, tgt, updated_relationship_data)

    # Update relationship in vector database
    rel_vdb_id = compute_mdhash_id(src + tgt, prefix="rel-")
    rel_vdb_id_reverse = compute_mdhash_id(tgt + src, prefix="rel-")

    # Delete old vector records first (both directions to be safe)
    try:
        await relationships_vdb.delete([rel_vdb_id, rel_vdb_id_reverse])
    except Exception as e:
        logger.debug(
            f"Could not delete old relationship vector records {rel_vdb_id}, {rel_vdb_id_reverse}: {e}"
        )

    # Insert new vector record
    rel_content = f"{combined_keywords}\t{src}\n{tgt}\n{final_description}"
    await relationships_vdb.upsert(
        {
            rel_vdb_id: {
                "src_id": src,
                "tgt_id": tgt,
                "source_id": updated_relationship_data["source_id"],
                "content": rel_content,
                "keywords": combined_keywords,
                "description": final_description,
                "weight": weight,
                "file_path": updated_relationship_data["file_path"],
            }
        }
    )


# CUSTOM: Node merge aggregates structural provenance (section_paths, section_node_ids,
# docling_refs, block_ids, artifact manifest, page span) and feeds citation-aware entity embeddings.
async def _merge_nodes_then_upsert(
    entity_name: str,
    nodes_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
    pipeline_status: dict = None,
    pipeline_status_lock=None,
    llm_response_cache: BaseKVStorage | None = None,
):
    """Get existing nodes from knowledge graph use name,if exists, merge data, else create, then upsert."""
    already_entity_types = []
    already_source_ids = []
    already_description = []
    already_file_paths = []
    already_section_paths = []
    already_section_node_ids = []
    already_docling_refs = []
    already_block_ids = []
    already_artifact_manifest_paths = []
    already_page_starts = []
    already_page_ends = []

    already_node = await knowledge_graph_inst.get_node(entity_name)
    if already_node:
        already_entity_types.append(already_node["entity_type"])
        already_source_ids.extend(
            split_string_by_multi_markers(already_node["source_id"], [GRAPH_FIELD_SEP])
        )
        already_file_paths.extend(
            split_string_by_multi_markers(already_node["file_path"], [GRAPH_FIELD_SEP])
        )
        already_description.append(already_node["description"])
        already_section_paths.extend(already_node.get("section_paths") or [])
        already_section_node_ids.extend(already_node.get("section_node_ids") or [])
        already_docling_refs.extend(already_node.get("docling_refs") or [])
        already_block_ids.extend(already_node.get("block_ids") or [])
        if already_node.get("artifact_manifest_path"):
            already_artifact_manifest_paths.append(already_node["artifact_manifest_path"])
        if already_node.get("page_start") is not None:
            already_page_starts.append(already_node["page_start"])
        if already_node.get("page_end") is not None:
            already_page_ends.append(already_node["page_end"])

    entity_type = sorted(
        Counter(
            [dp["entity_type"] for dp in nodes_data] + already_entity_types
        ).items(),
        key=lambda x: x[1],
        reverse=True,
    )[0][0]
    description = GRAPH_FIELD_SEP.join(
        sorted(set([dp["description"] for dp in nodes_data] + already_description))
    )
    source_id = GRAPH_FIELD_SEP.join(
        set([dp["source_id"] for dp in nodes_data] + already_source_ids)
    )
    file_path = GRAPH_FIELD_SEP.join(
        set([dp["file_path"] for dp in nodes_data] + already_file_paths)
    )
    section_paths = _merge_structural_values(nodes_data, "section_path")
    section_paths = _merge_structural_values(
        [{"section_path": value} for value in section_paths + already_section_paths],
        "section_path",
    )
    section_node_ids = _merge_structural_values(nodes_data, "section_node_ids")
    section_node_ids = _merge_structural_values(
        [{"section_node_ids": section_node_ids + already_section_node_ids}],
        "section_node_ids",
    )
    docling_refs = _merge_structural_values(nodes_data, "docling_refs")
    docling_refs = _merge_structural_values(
        [{"docling_refs": docling_refs + already_docling_refs}],
        "docling_refs",
    )
    block_ids = _merge_structural_values(nodes_data, "block_ids")
    block_ids = _merge_structural_values(
        [{"block_ids": block_ids + already_block_ids}],
        "block_ids",
    )
    artifact_manifest_paths = _merge_structural_values(nodes_data, "artifact_manifest_path")
    artifact_manifest_paths = _merge_structural_values(
        [{"artifact_manifest_path": artifact_manifest_paths + already_artifact_manifest_paths}],
        "artifact_manifest_path",
    )
    page_start_values = nodes_data + [{"page_start": value} for value in already_page_starts]
    page_end_values = nodes_data + [{"page_end": value} for value in already_page_ends]
    page_start = _merge_page_value(page_start_values, "page_start", min)
    page_end = _merge_page_value(page_end_values, "page_end", max)

    force_llm_summary_on_merge = global_config["force_llm_summary_on_merge"]

    num_fragment = description.count(GRAPH_FIELD_SEP) + 1
    num_new_fragment = len(set([dp["description"] for dp in nodes_data]))

    if num_fragment > 1:
        if num_fragment >= force_llm_summary_on_merge:
            status_message = f"LLM merge N: {entity_name} | {num_new_fragment}+{num_fragment-num_new_fragment}"
            logger.info(status_message)
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)
            description = await _handle_entity_relation_summary(
                entity_name,
                description,
                global_config,
                llm_response_cache,
            )
        else:
            status_message = f"Merge N: {entity_name} | {num_new_fragment}+{num_fragment-num_new_fragment}"
            logger.info(status_message)
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)

    node_data = dict(
        entity_id=entity_name,
        entity_type=entity_type,
        description=description,
        source_id=source_id,
        file_path=file_path,
        section_paths=section_paths,
        section_node_ids=section_node_ids,
        docling_refs=docling_refs,
        block_ids=block_ids,
        artifact_manifest_path=artifact_manifest_paths[0] if artifact_manifest_paths else None,
        page_start=page_start,
        page_end=page_end,
        created_at=int(time.time()),
    )
    await knowledge_graph_inst.upsert_node(
        entity_name,
        node_data=node_data,
    )
    node_data["entity_name"] = entity_name
    return node_data


# CUSTOM: Edge merge mirrors node structural fields so relationship vectors and graph edges
# preserve section/page/artifact metadata alongside descriptions.
async def _merge_edges_then_upsert(
    src_id: str,
    tgt_id: str,
    edges_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
    pipeline_status: dict = None,
    pipeline_status_lock=None,
    llm_response_cache: BaseKVStorage | None = None,
):
    if src_id == tgt_id:
        return None

    already_weights = []
    already_source_ids = []
    already_description = []
    already_keywords = []
    already_file_paths = []
    already_section_paths = []
    already_section_node_ids = []
    already_docling_refs = []
    already_block_ids = []
    already_artifact_manifest_paths = []
    already_page_starts = []
    already_page_ends = []

    if await knowledge_graph_inst.has_edge(src_id, tgt_id):
        already_edge = await knowledge_graph_inst.get_edge(src_id, tgt_id)
        # Handle the case where get_edge returns None or missing fields
        if already_edge:
            # Get weight with default 0.0 if missing
            already_weights.append(already_edge.get("weight", 0.0))

            # Get source_id with empty string default if missing or None
            if already_edge.get("source_id") is not None:
                already_source_ids.extend(
                    split_string_by_multi_markers(
                        already_edge["source_id"], [GRAPH_FIELD_SEP]
                    )
                )

            # Get file_path with empty string default if missing or None
            if already_edge.get("file_path") is not None:
                already_file_paths.extend(
                    split_string_by_multi_markers(
                        already_edge["file_path"], [GRAPH_FIELD_SEP]
                    )
                )

            # Get description with empty string default if missing or None
            if already_edge.get("description") is not None:
                already_description.append(already_edge["description"])

            # Get keywords with empty string default if missing or None
            if already_edge.get("keywords") is not None:
                already_keywords.extend(
                    split_string_by_multi_markers(
                        already_edge["keywords"], [GRAPH_FIELD_SEP]
                    )
                )
            already_section_paths.extend(already_edge.get("section_paths") or [])
            if already_edge.get("section_path"):
                already_section_paths.append(already_edge["section_path"])
            already_section_node_ids.extend(already_edge.get("section_node_ids") or [])
            already_docling_refs.extend(already_edge.get("docling_refs") or [])
            already_block_ids.extend(already_edge.get("block_ids") or [])
            if already_edge.get("artifact_manifest_path"):
                already_artifact_manifest_paths.append(already_edge["artifact_manifest_path"])
            if already_edge.get("page_start") is not None:
                already_page_starts.append(already_edge["page_start"])
            if already_edge.get("page_end") is not None:
                already_page_ends.append(already_edge["page_end"])

    # Process edges_data with None checks
    weight = sum([dp["weight"] for dp in edges_data] + already_weights)
    description = GRAPH_FIELD_SEP.join(
        sorted(
            set(
                [dp["description"] for dp in edges_data if dp.get("description")]
                + already_description
            )
        )
    )

    # Split all existing and new keywords into individual terms, then combine and deduplicate
    all_keywords = set()
    # Process already_keywords (which are comma-separated)
    for keyword_str in already_keywords:
        if keyword_str:  # Skip empty strings
            all_keywords.update(k.strip() for k in keyword_str.split(",") if k.strip())
    # Process new keywords from edges_data
    for edge in edges_data:
        if edge.get("keywords"):
            all_keywords.update(
                k.strip() for k in edge["keywords"].split(",") if k.strip()
            )
    # Join all unique keywords with commas
    keywords = ",".join(sorted(all_keywords))

    source_id = GRAPH_FIELD_SEP.join(
        set(
            [dp["source_id"] for dp in edges_data if dp.get("source_id")]
            + already_source_ids
        )
    )
    file_path = GRAPH_FIELD_SEP.join(
        set(
            [dp["file_path"] for dp in edges_data if dp.get("file_path")]
            + already_file_paths
        )
    )
    section_paths = _merge_structural_values(edges_data, "section_path")
    section_paths = _merge_structural_values(
        [{"section_path": value} for value in section_paths + already_section_paths],
        "section_path",
    )
    section_node_ids = _merge_structural_values(edges_data, "section_node_ids")
    section_node_ids = _merge_structural_values(
        [{"section_node_ids": section_node_ids + already_section_node_ids}],
        "section_node_ids",
    )
    docling_refs = _merge_structural_values(edges_data, "docling_refs")
    docling_refs = _merge_structural_values(
        [{"docling_refs": docling_refs + already_docling_refs}],
        "docling_refs",
    )
    block_ids = _merge_structural_values(edges_data, "block_ids")
    block_ids = _merge_structural_values(
        [{"block_ids": block_ids + already_block_ids}],
        "block_ids",
    )
    artifact_manifest_paths = _merge_structural_values(edges_data, "artifact_manifest_path")
    artifact_manifest_paths = _merge_structural_values(
        [{"artifact_manifest_path": artifact_manifest_paths + already_artifact_manifest_paths}],
        "artifact_manifest_path",
    )
    page_start_values = edges_data + [{"page_start": value} for value in already_page_starts]
    page_end_values = edges_data + [{"page_end": value} for value in already_page_ends]
    page_start = _merge_page_value(page_start_values, "page_start", min)
    page_end = _merge_page_value(page_end_values, "page_end", max)

    for need_insert_id in [src_id, tgt_id]:
        if await knowledge_graph_inst.has_node(need_insert_id):
            # This is so that the initial check for the existence of the node need not be locked
            continue
        async with get_graph_db_lock_keyed([need_insert_id], enable_logging=False):
            if not (await knowledge_graph_inst.has_node(need_insert_id)):
                # # Discard this edge if the node does not exist
                # if need_insert_id == src_id:
                #     logger.warning(
                #         f"Discard edge: {src_id} - {tgt_id} | Source node missing"
                #     )
                # else:
                #     logger.warning(
                #         f"Discard edge: {src_id} - {tgt_id} | Target node missing"
                #     )
                # return None
                await knowledge_graph_inst.upsert_node(
                    need_insert_id,
                    node_data={
                        "entity_id": need_insert_id,
                        "source_id": source_id,
                        "description": description,
                        "entity_type": "UNKNOWN",
                        "file_path": file_path,
                        "created_at": int(time.time()),
                    },
                )

    force_llm_summary_on_merge = global_config["force_llm_summary_on_merge"]

    num_fragment = description.count(GRAPH_FIELD_SEP) + 1
    num_new_fragment = len(
        set([dp["description"] for dp in edges_data if dp.get("description")])
    )

    if num_fragment > 1:
        if num_fragment >= force_llm_summary_on_merge:
            status_message = f"LLM merge E: {src_id} - {tgt_id} | {num_new_fragment}+{num_fragment-num_new_fragment}"
            logger.info(status_message)
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)
            description = await _handle_entity_relation_summary(
                f"({src_id}, {tgt_id})",
                description,
                global_config,
                llm_response_cache,
            )
        else:
            status_message = f"Merge E: {src_id} - {tgt_id} | {num_new_fragment}+{num_fragment-num_new_fragment}"
            logger.info(status_message)
            if pipeline_status is not None and pipeline_status_lock is not None:
                async with pipeline_status_lock:
                    pipeline_status["latest_message"] = status_message
                    pipeline_status["history_messages"].append(status_message)

    await knowledge_graph_inst.upsert_edge(
        src_id,
        tgt_id,
        edge_data=dict(
            weight=weight,
            description=description,
            keywords=keywords,
            source_id=source_id,
            file_path=file_path,
            section_paths=section_paths,
            section_node_ids=section_node_ids,
            docling_refs=docling_refs,
            block_ids=block_ids,
            artifact_manifest_path=artifact_manifest_paths[0] if artifact_manifest_paths else None,
            page_start=page_start,
            page_end=page_end,
            created_at=int(time.time()),
        ),
    )

    edge_data = dict(
        src_id=src_id,
        tgt_id=tgt_id,
        description=description,
        keywords=keywords,
        source_id=source_id,
        file_path=file_path,
        section_paths=section_paths,
        section_node_ids=section_node_ids,
        docling_refs=docling_refs,
        block_ids=block_ids,
        artifact_manifest_path=artifact_manifest_paths[0] if artifact_manifest_paths else None,
        page_start=page_start,
        page_end=page_end,
        created_at=int(time.time()),
    )

    return edge_data


# CUSTOM: After collecting extractions, synthesizes section anchor entities/edges, uses
# get_graph_db_lock_keyed for merges, and upserts vectors with structural embedding text.
async def merge_nodes_and_edges(
    chunk_results: list,
    knowledge_graph_inst: BaseGraphStorage,
    entity_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    global_config: dict[str, str],
    pipeline_status: dict = None,
    pipeline_status_lock=None,
    llm_response_cache: BaseKVStorage | None = None,
    current_file_number: int = 0,
    total_files: int = 0,
    file_path: str = "unknown_source",
) -> None:
    """Merge nodes and edges from extraction results

    Args:
        chunk_results: List of tuples (maybe_nodes, maybe_edges) containing extracted entities and relationships
        knowledge_graph_inst: Knowledge graph storage
        entity_vdb: Entity vector database
        relationships_vdb: Relationship vector database
        global_config: Global configuration
        pipeline_status: Pipeline status dictionary
        pipeline_status_lock: Lock for pipeline status
        llm_response_cache: LLM response cache
    """

    # Collect all nodes and edges from all chunks
    all_nodes = defaultdict(list)
    all_edges = defaultdict(list)

    for maybe_nodes, maybe_edges in chunk_results:
        # Collect nodes
        for entity_name, entities in maybe_nodes.items():
            all_nodes[entity_name].extend(entities)

        # Collect edges with sorted keys for undirected graph
        for edge_key, edges in maybe_edges.items():
            sorted_edge_key = tuple(sorted(edge_key))
            all_edges[sorted_edge_key].extend(edges)

    addon_params = global_config.get("addon_params", {}) if global_config else {}
    if addon_params.get("enable_section_anchor_kg", False):
        _add_section_anchor_nodes_and_edges(all_nodes, all_edges)

    # Centralized processing of all nodes and edges
    total_entities_count = len(all_nodes)
    total_relations_count = len(all_edges)

    # Merge nodes and edges
    log_message = f"Merging stage {current_file_number}/{total_files}: {file_path}"
    logger.info(log_message)
    async with pipeline_status_lock:
        pipeline_status["latest_message"] = log_message
        pipeline_status["history_messages"].append(log_message)

    # Process and update all entities and relationships in parallel
    log_message = f"Processing: {total_entities_count} entities and {total_relations_count} relations"
    logger.info(log_message)
    async with pipeline_status_lock:
        pipeline_status["latest_message"] = log_message
        pipeline_status["history_messages"].append(log_message)

    # Get max async tasks limit from global_config for semaphore control
    llm_model_max_async = global_config.get("llm_model_max_async", 4)
    semaphore = asyncio.Semaphore(llm_model_max_async)

    async def _locked_process_entity_name(entity_name, entities):
        async with semaphore:
            async with get_graph_db_lock_keyed([entity_name], enable_logging=False):
                entity_data = await _merge_nodes_then_upsert(
                    entity_name,
                    entities,
                    knowledge_graph_inst,
                    global_config,
                    pipeline_status,
                    pipeline_status_lock,
                    llm_response_cache,
                )
                if entity_vdb is not None:
                    data_for_vdb = {
                        compute_mdhash_id(entity_data["entity_name"], prefix="ent-"): {
                            "entity_name": entity_data["entity_name"],
                            "entity_type": entity_data["entity_type"],
                            "content": _entity_embedding_content(entity_data),
                            "source_id": entity_data["source_id"],
                            "file_path": entity_data.get("file_path", "unknown_source"),
                        }
                    }
                    await entity_vdb.upsert(data_for_vdb)
                return entity_data

    async def _locked_process_edges(edge_key, edges):
        async with semaphore:
            async with get_graph_db_lock_keyed(
                f"{edge_key[0]}-{edge_key[1]}", enable_logging=False
            ):
                edge_data = await _merge_edges_then_upsert(
                    edge_key[0],
                    edge_key[1],
                    edges,
                    knowledge_graph_inst,
                    global_config,
                    pipeline_status,
                    pipeline_status_lock,
                    llm_response_cache,
                )
                if edge_data is None:
                    return None

                if relationships_vdb is not None:
                    data_for_vdb = {
                        compute_mdhash_id(
                            edge_data["src_id"] + edge_data["tgt_id"], prefix="rel-"
                        ): {
                            "src_id": edge_data["src_id"],
                            "tgt_id": edge_data["tgt_id"],
                            "keywords": edge_data["keywords"],
                            "content": _relationship_embedding_content(edge_data),
                            "source_id": edge_data["source_id"],
                            "file_path": edge_data.get("file_path", "unknown_source"),
                        }
                    }
                    await relationships_vdb.upsert(data_for_vdb)
                return edge_data

    # Create a single task queue for both entities and edges
    tasks = []

    # Add entity processing tasks
    for entity_name, entities in all_nodes.items():
        tasks.append(
            asyncio.create_task(_locked_process_entity_name(entity_name, entities))
        )

    # Add edge processing tasks
    for edge_key, edges in all_edges.items():
        tasks.append(asyncio.create_task(_locked_process_edges(edge_key, edges)))

    # Execute all tasks in parallel with semaphore control
    await asyncio.gather(*tasks)


# CUSTOM: Skips non-KG-extractable chunks, injects corpus ontology hints + per-chunk section
# context into prompts, and threads structural provenance into extracted nodes/edges.
async def extract_entities(
    chunks: dict[str, TextChunkSchema],
    global_config: dict[str, str],
    pipeline_status: dict = None,
    pipeline_status_lock=None,
    llm_response_cache: BaseKVStorage | None = None,
    text_chunks_storage: BaseKVStorage | None = None,
) -> list:
    use_llm_func: callable = global_config["llm_model_func"]
    entity_extract_max_gleaning = global_config["entity_extract_max_gleaning"]

    ordered_chunks = _kg_extractable_chunk_items(list(chunks.items()))
    if not ordered_chunks:
        return []
    addon_params = global_config["addon_params"]
    # add language and example number params to prompt
    language = addon_params.get(
        "language", PROMPTS["DEFAULT_LANGUAGE"]
    )
    entity_types = addon_params.get(
        "entity_types", PROMPTS["DEFAULT_ENTITY_TYPES"]
    )
    ontology_guidance = _resolve_ontology_guidance(addon_params, ordered_chunks)
    example_number = addon_params.get("example_number", None)
    if example_number and example_number < len(PROMPTS["entity_extraction_examples"]):
        examples = "\n".join(
            PROMPTS["entity_extraction_examples"][: int(example_number)]
        )
    else:
        examples = "\n".join(PROMPTS["entity_extraction_examples"])

    example_context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        entity_types=", ".join(entity_types),
        language=language,
    )
    # add example's format
    examples = examples.format(**example_context_base)

    entity_extract_prompt = PROMPTS["entity_extraction"]
    context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        entity_types=",".join(entity_types),
        entity_type_descriptions=PROMPTS["DEFAULT_ENTITY_TYPE_DESCRIPTIONS"],
        ontology_guidance=ontology_guidance,
        section_context="Section context is supplied per chunk.",
        examples=examples,
        language=language,
    )

    continue_prompt = PROMPTS["entity_continue_extraction"].format(**context_base)
    if_loop_prompt = PROMPTS["entity_if_loop_extraction"]

    processed_chunks = 0
    total_chunks = len(ordered_chunks)

    async def _process_extraction_result(
        result: str,
        chunk_key: str,
        file_path: str = "unknown_source",
        section_path: str | None = None,
        provenance: dict[str, Any] | None = None,
    ):
        """Process a single extraction result (either initial or gleaning)
        Args:
            result (str): The extraction result to process
            chunk_key (str): The chunk key for source tracking
            file_path (str): The file path for citation
        Returns:
            tuple: (nodes_dict, edges_dict) containing the extracted entities and relationships
        """
        maybe_nodes = defaultdict(list)
        maybe_edges = defaultdict(list)

        records = split_string_by_multi_markers(
            result,
            [context_base["record_delimiter"], context_base["completion_delimiter"]],
        )

        for record in records:
            record = re.search(r"\((.*)\)", record)
            if record is None:
                continue
            record = record.group(1)
            record_attributes = split_string_by_multi_markers(
                record, [context_base["tuple_delimiter"]]
            )

            if_entities = await _handle_single_entity_extraction(
                record_attributes, chunk_key, file_path, section_path, provenance
            )
            if if_entities is not None:
                maybe_nodes[if_entities["entity_name"]].append(if_entities)
                continue

            if_relation = await _handle_single_relationship_extraction(
                record_attributes, chunk_key, file_path, section_path, provenance
            )
            if if_relation is not None:
                maybe_edges[(if_relation["src_id"], if_relation["tgt_id"])].append(
                    if_relation
                )

        return maybe_nodes, maybe_edges

    async def _process_single_content(chunk_key_dp: tuple[str, TextChunkSchema]):
        """Process a single chunk
        Args:
            chunk_key_dp (tuple[str, TextChunkSchema]):
                ("chunk-xxxxxx", {"tokens": int, "content": str, "full_doc_id": str, "chunk_order_index": int})
        Returns:
            tuple: (maybe_nodes, maybe_edges) containing extracted entities and relationships
        """
        nonlocal processed_chunks
        chunk_key = chunk_key_dp[0]
        chunk_dp = chunk_key_dp[1]
        content = chunk_dp["content"]
        # Get file path from chunk data or use default
        file_path = chunk_dp.get("file_path", "unknown_source")
        section_path = chunk_dp.get("section_path")
        provenance = _chunk_structural_provenance(chunk_dp)

        # Create cache keys collector for batch processing
        cache_keys_collector = []

        # Get initial extraction
        section_context = _build_section_context(chunk_dp)
        hint_prompt = entity_extract_prompt.format(
            **{
                **context_base,
                "input_text": content,
                "section_context": section_context,
            }
        )

        final_result = await use_llm_func_with_cache(
            hint_prompt,
            use_llm_func,
            llm_response_cache=llm_response_cache,
            cache_type="extract",
            chunk_id=chunk_key,
            cache_keys_collector=cache_keys_collector,
        )

        # Store LLM cache reference in chunk (will be handled by use_llm_func_with_cache)
        history = pack_user_ass_to_openai_messages(hint_prompt, final_result)

        # Process initial extraction with file path
        maybe_nodes, maybe_edges = await _process_extraction_result(
            final_result, chunk_key, file_path, section_path, provenance
        )

        # Process additional gleaning results
        for now_glean_index in range(entity_extract_max_gleaning):
            glean_result = await use_llm_func_with_cache(
                continue_prompt,
                use_llm_func,
                llm_response_cache=llm_response_cache,
                history_messages=history,
                cache_type="extract",
                chunk_id=chunk_key,
                cache_keys_collector=cache_keys_collector,
            )

            history += pack_user_ass_to_openai_messages(continue_prompt, glean_result)

            # Process gleaning result separately with file path
            glean_nodes, glean_edges = await _process_extraction_result(
                glean_result, chunk_key, file_path, section_path, provenance
            )

            # Merge results - only add entities and edges with new names
            for entity_name, entities in glean_nodes.items():
                if (
                    entity_name not in maybe_nodes
                ):  # Only accetp entities with new name in gleaning stage
                    maybe_nodes[entity_name].extend(entities)
            for edge_key, edges in glean_edges.items():
                if (
                    edge_key not in maybe_edges
                ):  # Only accetp edges with new name in gleaning stage
                    maybe_edges[edge_key].extend(edges)

            if now_glean_index == entity_extract_max_gleaning - 1:
                break

            if_loop_result: str = await use_llm_func_with_cache(
                if_loop_prompt,
                use_llm_func,
                llm_response_cache=llm_response_cache,
                history_messages=history,
                cache_type="extract",
                cache_keys_collector=cache_keys_collector,
            )
            if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
            if if_loop_result != "yes":
                break

        # Batch update chunk's llm_cache_list with all collected cache keys
        if cache_keys_collector and text_chunks_storage:
            await update_chunk_cache_list(
                chunk_key,
                text_chunks_storage,
                cache_keys_collector,
                "entity_extraction",
            )

        processed_chunks += 1
        entities_count = len(maybe_nodes)
        relations_count = len(maybe_edges)
        log_message = f"Chunk {processed_chunks} of {total_chunks} extracted {entities_count} Ent + {relations_count} Rel"
        logger.info(log_message)
        if pipeline_status is not None:
            async with pipeline_status_lock:
                pipeline_status["latest_message"] = log_message
                pipeline_status["history_messages"].append(log_message)

        # Return the extracted nodes and edges for centralized processing
        return maybe_nodes, maybe_edges

    # Get max async tasks limit from global_config
    llm_model_max_async = global_config.get("llm_model_max_async", 4)
    semaphore = asyncio.Semaphore(llm_model_max_async)

    async def _process_with_semaphore(chunk):
        async with semaphore:
            return await _process_single_content(chunk)

    tasks = []
    for c in ordered_chunks:
        task = asyncio.create_task(_process_with_semaphore(c))
        tasks.append(task)

    # Wait for tasks to complete or for the first exception to occur
    # This allows us to cancel remaining tasks if any task fails
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    # Check if any task raised an exception
    for task in done:
        if task.exception():
            # If a task failed, cancel all pending tasks
            # This prevents unnecessary processing since the parent function will abort anyway
            for pending_task in pending:
                pending_task.cancel()

            # Wait for cancellation to complete
            if pending:
                await asyncio.wait(pending)

            # Re-raise the exception to notify the caller
            raise task.exception()

    # If all tasks completed successfully, collect results
    chunk_results = [task.result() for task in tasks]

    # Return the chunk_results for later processing in merge_nodes_and_edges
    return chunk_results


# CUSTOM: Prompt assembly uses get_conversation_turns for multi-turn chat history (not in upstream operate).
async def kg_query(
    query: str,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
    global_config: dict[str, str],
    hashing_kv: BaseKVStorage | None = None,
    system_prompt: str | None = None,
    chunks_vdb: BaseVectorStorage = None,
) -> str | AsyncIterator[str]:
    if query_param.model_func:
        use_model_func = query_param.model_func
    else:
        use_model_func = global_config["llm_model_func"]
        # Apply higher priority (5) to query relation LLM function
        use_model_func = partial(use_model_func, _priority=5)

    # Handle cache
    args_hash = compute_args_hash(query_param.mode, query)
    cached_response, quantized, min_val, max_val = await handle_cache(
        hashing_kv, args_hash, query, query_param.mode, cache_type="query"
    )
    if cached_response is not None:
        return cached_response

    hl_keywords, ll_keywords = await get_keywords_from_query(
        query, query_param, global_config, hashing_kv
    )

    logger.debug(f"High-level keywords: {hl_keywords}")
    logger.debug(f"Low-level  keywords: {ll_keywords}")

    # Handle empty keywords
    if hl_keywords == [] and ll_keywords == []:
        logger.warning("low_level_keywords and high_level_keywords is empty")
        return PROMPTS["fail_response"]
    if ll_keywords == [] and query_param.mode in ["local", "hybrid"]:
        logger.warning(
            "low_level_keywords is empty, switching from %s mode to global mode",
            query_param.mode,
        )
        query_param.mode = "global"
    if hl_keywords == [] and query_param.mode in ["global", "hybrid"]:
        logger.warning(
            "high_level_keywords is empty, switching from %s mode to local mode",
            query_param.mode,
        )
        query_param.mode = "local"

    ll_keywords_str = ", ".join(ll_keywords) if ll_keywords else ""
    hl_keywords_str = ", ".join(hl_keywords) if hl_keywords else ""

    # Build context
    context = await _build_query_context(
        query,
        ll_keywords_str,
        hl_keywords_str,
        knowledge_graph_inst,
        entities_vdb,
        relationships_vdb,
        text_chunks_db,
        query_param,
        chunks_vdb,
    )

    if query_param.only_need_context:
        return context if context is not None else PROMPTS["fail_response"]
    if context is None:
        return PROMPTS["fail_response"]

    # Process conversation history
    history_context = ""
    if query_param.conversation_history:
        history_context = get_conversation_turns(
            query_param.conversation_history, query_param.history_turns
        )

    # Build system prompt
    user_prompt = (
        query_param.user_prompt
        if query_param.user_prompt
        else PROMPTS["DEFAULT_USER_PROMPT"]
    )
    sys_prompt_temp = system_prompt if system_prompt else PROMPTS["rag_response"]
    sys_prompt = sys_prompt_temp.format(
        context_data=context,
        response_type=query_param.response_type,
        history=history_context,
        user_prompt=user_prompt,
    )

    if query_param.only_need_prompt:
        return sys_prompt

    tokenizer: Tokenizer = global_config["tokenizer"]
    len_of_prompts = len(tokenizer.encode(query + sys_prompt))
    logger.debug(f"[kg_query]Prompt Tokens: {len_of_prompts}")

    response = await use_model_func(
        query,
        system_prompt=sys_prompt,
        stream=query_param.stream,
    )
    if isinstance(response, str) and len(response) > len(sys_prompt):
        response = (
            response.replace(sys_prompt, "")
            .replace("user", "")
            .replace("model", "")
            .replace(query, "")
            .replace("<system>", "")
            .replace("</system>", "")
            .strip()
        )

    if hashing_kv.global_config.get("enable_llm_cache"):
        # Save to cache
        await save_to_cache(
            hashing_kv,
            CacheData(
                args_hash=args_hash,
                content=response,
                prompt=query,
                quantized=quantized,
                min_val=min_val,
                max_val=max_val,
                mode=query_param.mode,
                cache_type="query",
            ),
        )

    return response


# CUSTOM: Non-streaming retrieval API — returns structured entities/relationships/chunks + keyword meta
# without calling the answer LLM (for UI inspection and downstream orchestration).
async def kg_retrieve(
    query: str,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
    global_config: dict[str, str],
    hashing_kv: BaseKVStorage | None = None,
    chunks_vdb: BaseVectorStorage = None,
) -> dict[str, Any]:
    hl_keywords, ll_keywords = await get_keywords_from_query(
        query, query_param, global_config, hashing_kv
    )

    logger.debug(f"High-level keywords: {hl_keywords}")
    logger.debug(f"Low-level  keywords: {ll_keywords}")

    if hl_keywords == [] and ll_keywords == []:
        logger.warning("low_level_keywords and high_level_keywords is empty")
        return _build_retrieval_context(
            query=query,
            mode=query_param.mode,
            entities=[],
            relationships=[],
            chunks=[],
        )
    if ll_keywords == [] and query_param.mode in ["local", "hybrid"]:
        logger.warning(
            "low_level_keywords is empty, switching from %s mode to global mode",
            query_param.mode,
        )
        query_param.mode = "global"
    if hl_keywords == [] and query_param.mode in ["global", "hybrid"]:
        logger.warning(
            "high_level_keywords is empty, switching from %s mode to local mode",
            query_param.mode,
        )
        query_param.mode = "local"

    ll_keywords_str = ", ".join(ll_keywords) if ll_keywords else ""
    hl_keywords_str = ", ".join(hl_keywords) if hl_keywords else ""

    context = await _build_query_context(
        query,
        ll_keywords_str,
        hl_keywords_str,
        knowledge_graph_inst,
        entities_vdb,
        relationships_vdb,
        text_chunks_db,
        query_param,
        chunks_vdb,
        return_structured=True,
    )
    if context is None:
        context = _build_retrieval_context(
            query=query,
            mode=query_param.mode,
            entities=[],
            relationships=[],
            chunks=[],
        )
    context["retrieval_meta"]["high_level_keywords"] = hl_keywords
    context["retrieval_meta"]["low_level_keywords"] = ll_keywords
    return context


async def get_keywords_from_query(
    query: str,
    query_param: QueryParam,
    global_config: dict[str, str],
    hashing_kv: BaseKVStorage | None = None,
) -> tuple[list[str], list[str]]:
    """
    Retrieves high-level and low-level keywords for RAG operations.

    This function checks if keywords are already provided in query parameters,
    and if not, extracts them from the query text using LLM.

    Args:
        query: The user's query text
        query_param: Query parameters that may contain pre-defined keywords
        global_config: Global configuration dictionary
        hashing_kv: Optional key-value storage for caching results

    Returns:
        A tuple containing (high_level_keywords, low_level_keywords)
    """
    # Check if pre-defined keywords are already provided
    if query_param.hl_keywords or query_param.ll_keywords:
        return query_param.hl_keywords, query_param.ll_keywords

    # Extract keywords using extract_keywords_only function which already supports conversation history
    hl_keywords, ll_keywords = await extract_keywords_only(
        query, query_param, global_config, hashing_kv
    )
    return hl_keywords, ll_keywords


async def extract_keywords_only(
    text: str,
    param: QueryParam,
    global_config: dict[str, str],
    hashing_kv: BaseKVStorage | None = None,
) -> tuple[list[str], list[str]]:
    """
    Extract high-level and low-level keywords from the given 'text' using the LLM.
    This method does NOT build the final RAG context or provide a final answer.
    It ONLY extracts keywords (hl_keywords, ll_keywords).
    """

    # 1. Handle cache if needed - add cache type for keywords
    args_hash = compute_args_hash(param.mode, text)
    cached_response, quantized, min_val, max_val = await handle_cache(
        hashing_kv, args_hash, text, param.mode, cache_type="keywords"
    )
    if cached_response is not None:
        try:
            keywords_data = json.loads(cached_response)
            return keywords_data["high_level_keywords"], keywords_data[
                "low_level_keywords"
            ]
        except (json.JSONDecodeError, KeyError):
            logger.warning(
                "Invalid cache format for keywords, proceeding with extraction"
            )

    # 2. Build the examples
    example_number = global_config["addon_params"].get("example_number", None)
    if example_number and example_number < len(PROMPTS["keywords_extraction_examples"]):
        examples = "\n".join(
            PROMPTS["keywords_extraction_examples"][: int(example_number)]
        )
    else:
        examples = "\n".join(PROMPTS["keywords_extraction_examples"])
    language = global_config["addon_params"].get(
        "language", PROMPTS["DEFAULT_LANGUAGE"]
    )

    # 3. Process conversation history
    history_context = ""
    if param.conversation_history:
        history_context = get_conversation_turns(
            param.conversation_history, param.history_turns
        )

    # 4. Build the keyword-extraction prompt
    kw_prompt = PROMPTS["keywords_extraction"].format(
        query=text, examples=examples, language=language, history=history_context
    )

    tokenizer: Tokenizer = global_config["tokenizer"]
    len_of_prompts = len(tokenizer.encode(kw_prompt))
    logger.debug(f"[kg_query]Prompt Tokens: {len_of_prompts}")

    # 5. Call the LLM for keyword extraction
    if param.model_func:
        use_model_func = param.model_func
    else:
        use_model_func = global_config["llm_model_func"]
        # Apply higher priority (5) to query relation LLM function
        use_model_func = partial(use_model_func, _priority=5)

    result = await use_model_func(kw_prompt, keyword_extraction=True)

    # 6. Parse out JSON from the LLM response
    result = remove_think_tags(result)
    match = re.search(r"\{.*?\}", result, re.DOTALL)
    if not match:
        logger.error("No JSON-like structure found in the LLM respond.")
        return [], []
    try:
        keywords_data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return [], []

    hl_keywords = keywords_data.get("high_level_keywords", [])
    ll_keywords = keywords_data.get("low_level_keywords", [])

    # 7. Cache only the processed keywords with cache type
    if hl_keywords or ll_keywords:
        cache_data = {
            "high_level_keywords": hl_keywords,
            "low_level_keywords": ll_keywords,
        }
        if hashing_kv.global_config.get("enable_llm_cache"):
            await save_to_cache(
                hashing_kv,
                CacheData(
                    args_hash=args_hash,
                    content=json.dumps(cache_data),
                    prompt=text,
                    quantized=quantized,
                    min_val=min_val,
                    max_val=max_val,
                    mode=param.mode,
                    cache_type="keywords",
                ),
            )

    return hl_keywords, ll_keywords


# CUSTOM: Vector hits are normalized to the same chunk/citation field shape as KV-stored chunks.
async def _get_vector_context(
    query: str,
    chunks_vdb: BaseVectorStorage,
    query_param: QueryParam,
) -> list[dict]:
    """
    Retrieve text chunks from the vector database without reranking or truncation.

    This function performs vector search to find relevant text chunks for a query.
    Reranking and truncation will be handled later in the unified processing.

    Args:
        query: The query string to search for
        chunks_vdb: Vector database containing document chunks
        query_param: Query parameters including chunk_top_k and ids

    Returns:
        List of text chunks with metadata
    """
    try:
        # Use chunk_top_k if specified, otherwise fall back to top_k
        search_top_k = query_param.chunk_top_k or query_param.top_k

        results = await chunks_vdb.query(query, top_k=search_top_k, ids=query_param.ids)
        if not results:
            return []

        valid_chunks = []
        for result in results:
            if "content" in result:
                chunk_with_metadata = {
                    "chunk_id": _chunk_id_from_result(result),
                    "content": result["content"],
                    "created_at": result.get("created_at", None),
                    "file_path": result.get("file_path", "unknown_source"),
                    "full_doc_id": result.get("full_doc_id"),
                    "distance": result.get("distance"),
                    "tokens": result.get("tokens"),
                    "chunk_order_index": result.get("chunk_order_index"),
                    "source_type": "vector",  # Mark the source type
                    # CUSTOM STRUCTURAL CHUNKING:
                    # Vector results now carry the same citation fields as text
                    # chunk storage so vector-only and mixed retrieval modes can
                    # show page/section/artifact references consistently.
                    **citation_fields_from_chunk(result),
                }
                valid_chunks.append(chunk_with_metadata)

        logger.info(
            f"Naive query: {len(valid_chunks)} chunks (chunk_top_k: {search_top_k})"
        )
        return valid_chunks

    except Exception as e:
        logger.error(f"Error in _get_vector_context: {e}")
        return []


# CUSTOM: Builds mixed retrieval (entity + relation + optional vector in "mix"), merges contexts with
# process_combine_contexts, runs fork process_chunks_unified, and can return structured dicts via return_structured.
async def _build_query_context(
    query: str,
    ll_keywords: str,
    hl_keywords: str,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
    chunks_vdb: BaseVectorStorage = None,
    return_structured: bool = False,
):
    logger.info(f"Process {os.getpid()} building query context...")

    # Collect all chunks from different sources
    all_chunks = []
    entities_context = []
    relations_context = []

    # Handle local and global modes
    if query_param.mode == "local":
        entities_context, relations_context, entity_chunks = await _get_node_data(
            ll_keywords,
            knowledge_graph_inst,
            entities_vdb,
            text_chunks_db,
            query_param,
        )
        all_chunks.extend(entity_chunks)

    elif query_param.mode == "global":
        entities_context, relations_context, relationship_chunks = await _get_edge_data(
            hl_keywords,
            knowledge_graph_inst,
            relationships_vdb,
            text_chunks_db,
            query_param,
        )
        all_chunks.extend(relationship_chunks)

    else:  # hybrid or mix mode
        ll_data = await _get_node_data(
            ll_keywords,
            knowledge_graph_inst,
            entities_vdb,
            text_chunks_db,
            query_param,
        )
        hl_data = await _get_edge_data(
            hl_keywords,
            knowledge_graph_inst,
            relationships_vdb,
            text_chunks_db,
            query_param,
        )

        (ll_entities_context, ll_relations_context, ll_chunks) = ll_data
        (hl_entities_context, hl_relations_context, hl_chunks) = hl_data

        # Collect chunks from entity and relationship sources
        all_chunks.extend(ll_chunks)
        all_chunks.extend(hl_chunks)

        # Get vector chunks if in mix mode
        if query_param.mode == "mix" and chunks_vdb:
            vector_chunks = await _get_vector_context(
                query,
                chunks_vdb,
                query_param,
            )
            all_chunks.extend(vector_chunks)

        # Combine entities and relations contexts
        entities_context = process_combine_contexts(
            hl_entities_context, ll_entities_context
        )
        relations_context = process_combine_contexts(
            hl_relations_context, ll_relations_context
        )

    # Process all chunks uniformly: deduplication, reranking, and token truncation
    processed_chunks = await process_chunks_unified(
        query=query,
        chunks=all_chunks,
        query_param=query_param,
        global_config=text_chunks_db.global_config,
        source_type="mixed",
    )
    processed_chunks, parent_context_meta = _attach_parent_context_to_chunks(
        processed_chunks,
        query_param=query_param,
        global_config=text_chunks_db.global_config,
    )

    # Build final text_units_context from processed chunks
    text_units_context = []
    for i, chunk in enumerate(processed_chunks):
        # CUSTOM STRUCTURAL CHUNKING:
        # Final context is the contract seen by downstream answer generation.
        # Include structural citation fields when present, but omit them for old
        # flat chunks instead of inventing fake pages or sections.
        text_units_context.append(
            {
                **_build_chunk_context(chunk, i + 1),
            }
        )

    logger.info(
        f"Final context: {len(entities_context)} entities, {len(relations_context)} relations, {len(text_units_context)} chunks"
    )

    if not entities_context and not relations_context and not text_units_context:
        return None

    context = _build_retrieval_context(
        query=query,
        mode=query_param.mode,
        entities=entities_context,
        relationships=relations_context,
        chunks=text_units_context,
    )
    context["retrieval_meta"].update(parent_context_meta)

    if return_structured:
        return context
    return _format_retrieval_context(context)


async def _get_node_data(
    query: str,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
):
    # get similar entities
    logger.info(
        f"Query nodes: {query}, top_k: {query_param.top_k}, cosine: {entities_vdb.cosine_better_than_threshold}"
    )

    results = await entities_vdb.query(
        query, top_k=query_param.top_k, ids=query_param.ids
    )

    if not len(results):
        return [], [], []

    # Extract all entity IDs from your results list
    node_ids = [r["entity_name"] for r in results]

    # Call the batch node retrieval and degree functions concurrently.
    nodes_dict, degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_nodes_batch(node_ids),
        knowledge_graph_inst.node_degrees_batch(node_ids),
    )

    # Now, if you need the node data and degree in order:
    node_datas = [nodes_dict.get(nid) for nid in node_ids]
    node_degrees = [degrees_dict.get(nid, 0) for nid in node_ids]

    if not all([n is not None for n in node_datas]):
        logger.warning("Some nodes are missing, maybe the storage is damaged")

    node_datas = [
        {
            **n,
            "entity_name": k["entity_name"],
            "rank": d,
            "created_at": k.get("created_at"),
        }
        for k, n, d in zip(results, node_datas, node_degrees)
        if n is not None
    ]  # what is this text_chunks_db doing.  dont remember it in airvx.  check the diagram.
    # get entitytext chunk
    use_text_units = await _find_most_related_text_unit_from_entities(
        node_datas,
        query_param,
        text_chunks_db,
        knowledge_graph_inst,
    )
    use_relations = await _find_most_related_edges_from_entities(
        node_datas,
        query_param,
        knowledge_graph_inst,
    )

    tokenizer: Tokenizer = text_chunks_db.global_config.get("tokenizer")
    len_node_datas = len(node_datas)
    node_datas = truncate_list_by_token_size(
        node_datas,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_local_context,
        tokenizer=tokenizer,
    )
    logger.debug(
        f"Truncate entities from {len_node_datas} to {len(node_datas)} (max tokens:{query_param.max_token_for_local_context})"
    )

    logger.info(
        f"Local query: {len(node_datas)} entites, {len(use_relations)} relations, {len(use_text_units)} chunks"
    )

    # build prompt
    entities_context = []
    for i, n in enumerate(node_datas):
        created_at = n.get("created_at", "UNKNOWN")
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from node data
        file_path = n.get("file_path", "unknown_source")

        entity_context = {
            "id": i + 1,
            "entity": n["entity_name"],
            "type": n.get("entity_type", "UNKNOWN"),
            "description": n.get("description", "UNKNOWN"),
            "rank": n["rank"],
            "created_at": created_at,
            "file_path": file_path,
            "section_path": n.get("section_path"),
            "section_paths": n.get("section_paths"),
            "page_start": n.get("page_start"),
            "page_end": n.get("page_end"),
        }
        entity_context["citation_label"] = _compact_citation_label(entity_context)
        entities_context.append(entity_context)

    relations_context = []
    for i, e in enumerate(use_relations):
        created_at = e.get("created_at", "UNKNOWN")
        # Convert timestamp to readable format
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from edge data
        file_path = e.get("file_path", "unknown_source")

        relation_context = {
            "id": i + 1,
            "entity1": e["src_tgt"][0],
            "entity2": e["src_tgt"][1],
            "description": e["description"],
            "keywords": e["keywords"],
            "weight": e["weight"],
            "rank": e["rank"],
            "created_at": created_at,
            "file_path": file_path,
            "section_path": e.get("section_path"),
            "section_paths": e.get("section_paths"),
            "page_start": e.get("page_start"),
            "page_end": e.get("page_end"),
        }
        relation_context["citation_label"] = _compact_citation_label(relation_context)
        relations_context.append(relation_context)

    return entities_context, relations_context, use_text_units


async def _find_most_related_text_unit_from_entities(
    node_datas: list[dict],
    query_param: QueryParam,
    text_chunks_db: BaseKVStorage,
    knowledge_graph_inst: BaseGraphStorage,
):
    text_units = [
        split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
        for dp in node_datas
        if dp["source_id"] is not None
    ]

    node_names = [dp["entity_name"] for dp in node_datas]
    batch_edges_dict = await knowledge_graph_inst.get_nodes_edges_batch(node_names)
    # Build the edges list in the same order as node_datas.
    edges = [batch_edges_dict.get(name, []) for name in node_names]

    all_one_hop_nodes = set()
    for this_edges in edges:
        if not this_edges:
            continue
        all_one_hop_nodes.update([e[1] for e in this_edges])

    all_one_hop_nodes = list(all_one_hop_nodes)

    # Batch retrieve one-hop node data using get_nodes_batch
    all_one_hop_nodes_data_dict = await knowledge_graph_inst.get_nodes_batch(
        all_one_hop_nodes
    )
    all_one_hop_nodes_data = [
        all_one_hop_nodes_data_dict.get(e) for e in all_one_hop_nodes
    ]

    # Add null check for node data
    all_one_hop_text_units_lookup = {
        k: set(split_string_by_multi_markers(v["source_id"], [GRAPH_FIELD_SEP]))
        for k, v in zip(all_one_hop_nodes, all_one_hop_nodes_data)
        if v is not None and "source_id" in v  # Add source_id check
    }

    all_text_units_lookup = {}
    tasks = []

    for index, (this_text_units, this_edges) in enumerate(zip(text_units, edges)):
        for c_id in this_text_units:
            if c_id not in all_text_units_lookup:
                all_text_units_lookup[c_id] = index
                tasks.append((c_id, index, this_edges))

    # Process in batches tasks at a time to avoid overwhelming resources
    batch_size = 5
    results = []

    for i in range(0, len(tasks), batch_size):
        batch_tasks = tasks[i : i + batch_size]
        batch_results = await asyncio.gather(
            *[text_chunks_db.get_by_id(c_id) for c_id, _, _ in batch_tasks]
        )
        results.extend(batch_results)

    for (c_id, index, this_edges), data in zip(tasks, results):
        all_text_units_lookup[c_id] = {
            "data": data,
            "order": index,
            "relation_counts": 0,
        }

        if this_edges:
            for e in this_edges:
                if (
                    e[1] in all_one_hop_text_units_lookup
                    and c_id in all_one_hop_text_units_lookup[e[1]]
                ):
                    all_text_units_lookup[c_id]["relation_counts"] += 1

    # Filter out None values and ensure data has content
    all_text_units = [
        {"id": k, **v}
        for k, v in all_text_units_lookup.items()
        if v is not None and v.get("data") is not None and "content" in v["data"]
    ]

    if not all_text_units:
        logger.warning("No valid text units found")
        return []

    # Sort by relation counts and order, but don't truncate
    all_text_units = sorted(
        all_text_units, key=lambda x: (x["order"], -x["relation_counts"])
    )

    logger.debug(f"Found {len(all_text_units)} entity-related chunks")

    # Add source type marking and return chunk data
    result_chunks = []
    for t in all_text_units:
        chunk_data = t["data"].copy()
        chunk_data["chunk_id"] = t["id"]
        chunk_data["source_type"] = "entity"
        result_chunks.append(chunk_data)

    return result_chunks


async def _find_most_related_edges_from_entities(
    node_datas: list[dict],
    query_param: QueryParam,
    knowledge_graph_inst: BaseGraphStorage,
):
    node_names = [dp["entity_name"] for dp in node_datas]
    batch_edges_dict = await knowledge_graph_inst.get_nodes_edges_batch(node_names)

    all_edges = []
    seen = set()

    for node_name in node_names:
        this_edges = batch_edges_dict.get(node_name, [])
        for e in this_edges:
            sorted_edge = tuple(sorted(e))
            if sorted_edge not in seen:
                seen.add(sorted_edge)
                all_edges.append(sorted_edge)

    # Prepare edge pairs in two forms:
    # For the batch edge properties function, use dicts.
    edge_pairs_dicts = [{"src": e[0], "tgt": e[1]} for e in all_edges]
    # For edge degrees, use tuples.
    edge_pairs_tuples = list(all_edges)  # all_edges is already a list of tuples

    # Call the batched functions concurrently.
    edge_data_dict, edge_degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_edges_batch(edge_pairs_dicts),
        knowledge_graph_inst.edge_degrees_batch(edge_pairs_tuples),
    )

    # Reconstruct edge_datas list in the same order as the deduplicated results.
    all_edges_data = []
    for pair in all_edges:
        edge_props = edge_data_dict.get(pair)
        if edge_props is not None:
            if "weight" not in edge_props:
                logger.warning(
                    f"Edge {pair} missing 'weight' attribute, using default value 0.0"
                )
                edge_props["weight"] = 0.0

            combined = {
                "src_tgt": pair,
                "rank": edge_degrees_dict.get(pair, 0),
                **edge_props,
            }
            all_edges_data.append(combined)

    tokenizer: Tokenizer = knowledge_graph_inst.global_config.get("tokenizer")
    all_edges_data = sorted(
        all_edges_data, key=lambda x: (x["rank"], x["weight"]), reverse=True
    )
    all_edges_data = truncate_list_by_token_size(
        all_edges_data,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_global_context,
        tokenizer=tokenizer,
    )

    logger.debug(
        f"Truncate relations from {len(all_edges)} to {len(all_edges_data)} (max tokens:{query_param.max_token_for_global_context})"
    )

    return all_edges_data


async def _get_edge_data(
    keywords,
    knowledge_graph_inst: BaseGraphStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
):
    logger.info(
        f"Query edges: {keywords}, top_k: {query_param.top_k}, cosine: {relationships_vdb.cosine_better_than_threshold}"
    )

    results = await relationships_vdb.query(
        keywords, top_k=query_param.top_k, ids=query_param.ids
    )

    if not len(results):
        return [], [], []

    # Prepare edge pairs in two forms:
    # For the batch edge properties function, use dicts.
    edge_pairs_dicts = [{"src": r["src_id"], "tgt": r["tgt_id"]} for r in results]
    # For edge degrees, use tuples.
    edge_pairs_tuples = [(r["src_id"], r["tgt_id"]) for r in results]

    # Call the batched functions concurrently.
    edge_data_dict, edge_degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_edges_batch(edge_pairs_dicts),
        knowledge_graph_inst.edge_degrees_batch(edge_pairs_tuples),
    )

    # Reconstruct edge_datas list in the same order as results.
    edge_datas = []
    for k in results:
        pair = (k["src_id"], k["tgt_id"])
        edge_props = edge_data_dict.get(pair)
        if edge_props is not None:
            if "weight" not in edge_props:
                logger.warning(
                    f"Edge {pair} missing 'weight' attribute, using default value 0.0"
                )
                edge_props["weight"] = 0.0

            # Use edge degree from the batch as rank.
            combined = {
                "src_id": k["src_id"],
                "tgt_id": k["tgt_id"],
                "rank": edge_degrees_dict.get(pair, k.get("rank", 0)),
                "created_at": k.get("created_at", None),
                **edge_props,
            }
            edge_datas.append(combined)

    tokenizer: Tokenizer = text_chunks_db.global_config.get("tokenizer")
    edge_datas = sorted(
        edge_datas, key=lambda x: (x["rank"], x["weight"]), reverse=True
    )
    edge_datas = truncate_list_by_token_size(
        edge_datas,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_global_context,
        tokenizer=tokenizer,
    )
    use_entities, use_text_units = await asyncio.gather(
        _find_most_related_entities_from_relationships(
            edge_datas,
            query_param,
            knowledge_graph_inst,
        ),
        _find_related_text_unit_from_relationships(
            edge_datas,
            query_param,
            text_chunks_db,
            knowledge_graph_inst,
        ),
    )
    logger.info(
        f"Global query: {len(use_entities)} entites, {len(edge_datas)} relations, {len(use_text_units)} chunks"
    )

    relations_context = []
    for i, e in enumerate(edge_datas):
        created_at = e.get("created_at", "UNKNOWN")
        # Convert timestamp to readable format
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from edge data
        file_path = e.get("file_path", "unknown_source")

        relation_context = {
            "id": i + 1,
            "entity1": e["src_id"],
            "entity2": e["tgt_id"],
            "description": e["description"],
            "keywords": e["keywords"],
            "weight": e["weight"],
            "rank": e["rank"],
            "created_at": created_at,
            "file_path": file_path,
            "section_path": e.get("section_path"),
            "section_paths": e.get("section_paths"),
            "page_start": e.get("page_start"),
            "page_end": e.get("page_end"),
        }
        relation_context["citation_label"] = _compact_citation_label(relation_context)
        relations_context.append(relation_context)

    entities_context = []
    for i, n in enumerate(use_entities):
        created_at = n.get("created_at", "UNKNOWN")
        # Convert timestamp to readable format
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from node data
        file_path = n.get("file_path", "unknown_source")

        entity_context = {
            "id": i + 1,
            "entity": n["entity_name"],
            "type": n.get("entity_type", "UNKNOWN"),
            "description": n.get("description", "UNKNOWN"),
            "rank": n["rank"],
            "created_at": created_at,
            "file_path": file_path,
            "section_path": n.get("section_path"),
            "section_paths": n.get("section_paths"),
            "page_start": n.get("page_start"),
            "page_end": n.get("page_end"),
        }
        entity_context["citation_label"] = _compact_citation_label(entity_context)
        entities_context.append(entity_context)

    text_units_context = []
    for i, t in enumerate(use_text_units):
        # CUSTOM STRUCTURAL CHUNKING:
        # Relationship/global retrieval loads chunks from text chunk storage.
        # Keep the same citation shape here that vector and mixed modes expose.
        text_units_context.append(
            {
                **_build_chunk_context(t, i + 1),
            }
        )
    return entities_context, relations_context, text_units_context


async def _find_most_related_entities_from_relationships(
    edge_datas: list[dict],
    query_param: QueryParam,
    knowledge_graph_inst: BaseGraphStorage,
):
    entity_names = []
    seen = set()

    for e in edge_datas:
        if e["src_id"] not in seen:
            entity_names.append(e["src_id"])
            seen.add(e["src_id"])
        if e["tgt_id"] not in seen:
            entity_names.append(e["tgt_id"])
            seen.add(e["tgt_id"])

    # Batch approach: Retrieve nodes and their degrees concurrently with one query each.
    nodes_dict, degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_nodes_batch(entity_names),
        knowledge_graph_inst.node_degrees_batch(entity_names),
    )

    # Rebuild the list in the same order as entity_names
    node_datas = []
    for entity_name in entity_names:
        node = nodes_dict.get(entity_name)
        degree = degrees_dict.get(entity_name, 0)
        if node is None:
            logger.warning(f"Node '{entity_name}' not found in batch retrieval.")
            continue
        # Combine the node data with the entity name and computed degree (as rank)
        combined = {**node, "entity_name": entity_name, "rank": degree}
        node_datas.append(combined)

    tokenizer: Tokenizer = knowledge_graph_inst.global_config.get("tokenizer")
    len_node_datas = len(node_datas)
    node_datas = truncate_list_by_token_size(
        node_datas,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_local_context,
        tokenizer=tokenizer,
    )
    logger.debug(
        f"Truncate entities from {len_node_datas} to {len(node_datas)} (max tokens:{query_param.max_token_for_local_context})"
    )

    return node_datas


async def _find_related_text_unit_from_relationships(
    edge_datas: list[dict],
    query_param: QueryParam,
    text_chunks_db: BaseKVStorage,
    knowledge_graph_inst: BaseGraphStorage,
):
    text_units = [
        split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
        for dp in edge_datas
        if dp["source_id"] is not None
    ]
    all_text_units_lookup = {}

    async def fetch_chunk_data(c_id, index):
        if c_id not in all_text_units_lookup:
            chunk_data = await text_chunks_db.get_by_id(c_id)
            # Only store valid data
            if chunk_data is not None and "content" in chunk_data:
                all_text_units_lookup[c_id] = {
                    "data": chunk_data,
                    "order": index,
                }

    tasks = []
    for index, unit_list in enumerate(text_units):
        for c_id in unit_list:
            tasks.append(fetch_chunk_data(c_id, index))

    await asyncio.gather(*tasks)

    if not all_text_units_lookup:
        logger.warning("No valid text chunks found")
        return []

    all_text_units = [{"id": k, **v} for k, v in all_text_units_lookup.items()]
    all_text_units = sorted(all_text_units, key=lambda x: x["order"])

    # Ensure all text chunks have content
    valid_text_units = [
        t for t in all_text_units if t["data"] is not None and "content" in t["data"]
    ]

    if not valid_text_units:
        logger.warning("No valid text chunks after filtering")
        return []

    logger.debug(f"Found {len(valid_text_units)} relationship-related chunks")

    # Add source type marking and return chunk data
    result_chunks = []
    for t in valid_text_units:
        chunk_data = t["data"].copy()
        chunk_data["chunk_id"] = t["id"]
        chunk_data["source_type"] = "relationship"
        result_chunks.append(chunk_data)

    return result_chunks


# CUSTOM: Naive mode retrieval payload only — vector search + unified chunk processing as structured JSON.
async def naive_retrieve(
    query: str,
    chunks_vdb: BaseVectorStorage,
    query_param: QueryParam,
    global_config: dict[str, str],
) -> dict[str, Any]:
    chunks = await _get_vector_context(query, chunks_vdb, query_param)
    if chunks is None or len(chunks) == 0:
        return _build_retrieval_context(
            query=query,
            mode=query_param.mode,
            entities=[],
            relationships=[],
            chunks=[],
        )

    processed_chunks = await process_chunks_unified(
        query=query,
        chunks=chunks,
        query_param=query_param,
        global_config=global_config,
        source_type="vector",
    )
    processed_chunks, parent_context_meta = _attach_parent_context_to_chunks(
        processed_chunks,
        query_param=query_param,
        global_config=global_config,
    )
    text_units_context = [
        _build_chunk_context(chunk, i + 1) for i, chunk in enumerate(processed_chunks)
    ]
    context = _build_retrieval_context(
        query=query,
        mode=query_param.mode,
        entities=[],
        relationships=[],
        chunks=text_units_context,
    )
    context["retrieval_meta"].update(parent_context_meta)
    return context


# CUSTOM: Naive answer path uses structured chunk lists, optional conversation history, and _format_naive_context for only_need_context.
async def naive_query(
    query: str,
    chunks_vdb: BaseVectorStorage,
    query_param: QueryParam,
    global_config: dict[str, str],
    hashing_kv: BaseKVStorage | None = None,
    system_prompt: str | None = None,
) -> str | AsyncIterator[str]:
    if query_param.model_func:
        use_model_func = query_param.model_func
    else:
        use_model_func = global_config["llm_model_func"]
        # Apply higher priority (5) to query relation LLM function
        use_model_func = partial(use_model_func, _priority=5)

    # Handle cache
    args_hash = compute_args_hash(query_param.mode, query)
    cached_response, quantized, min_val, max_val = await handle_cache(
        hashing_kv, args_hash, query, query_param.mode, cache_type="query"
    )
    if cached_response is not None:
        return cached_response

    tokenizer: Tokenizer = global_config["tokenizer"]

    chunks = await _get_vector_context(query, chunks_vdb, query_param)

    if chunks is None or len(chunks) == 0:
        return PROMPTS["fail_response"]

    # Process chunks using unified processing
    processed_chunks = await process_chunks_unified(
        query=query,
        chunks=chunks,
        query_param=query_param,
        global_config=global_config,
        source_type="vector",
    )
    processed_chunks, parent_context_meta = _attach_parent_context_to_chunks(
        processed_chunks,
        query_param=query_param,
        global_config=global_config,
    )

    logger.info(f"Final context: {len(processed_chunks)} chunks")

    context = _build_retrieval_context(
        query=query,
        mode=query_param.mode,
        entities=[],
        relationships=[],
        chunks=[
            _build_chunk_context(chunk, i + 1)
            for i, chunk in enumerate(processed_chunks)
        ],
    )
    context["retrieval_meta"].update(parent_context_meta)
    text_units_str = _format_naive_context(context)
    if query_param.only_need_context:
        return text_units_str
    # Process conversation history
    history_context = ""
    if query_param.conversation_history:
        history_context = get_conversation_turns(
            query_param.conversation_history, query_param.history_turns
        )

    # Build system prompt
    user_prompt = (
        query_param.user_prompt
        if query_param.user_prompt
        else PROMPTS["DEFAULT_USER_PROMPT"]
    )
    sys_prompt_temp = system_prompt if system_prompt else PROMPTS["naive_rag_response"]
    sys_prompt = sys_prompt_temp.format(
        content_data=text_units_str,
        response_type=query_param.response_type,
        history=history_context,
        user_prompt=user_prompt,
    )

    if query_param.only_need_prompt:
        return sys_prompt

    len_of_prompts = len(tokenizer.encode(query + sys_prompt))
    logger.debug(f"[naive_query]Prompt Tokens: {len_of_prompts}")

    response = await use_model_func(
        query,
        system_prompt=sys_prompt,
        stream=query_param.stream,
    )

    if isinstance(response, str) and len(response) > len(sys_prompt):
        response = (
            response[len(sys_prompt) :]
            .replace(sys_prompt, "")
            .replace("user", "")
            .replace("model", "")
            .replace(query, "")
            .replace("<system>", "")
            .replace("</system>", "")
            .strip()
        )

    if hashing_kv.global_config.get("enable_llm_cache"):
        # Save to cache
        await save_to_cache(
            hashing_kv,
            CacheData(
                args_hash=args_hash,
                content=response,
                prompt=query,
                quantized=quantized,
                min_val=min_val,
                max_val=max_val,
                mode=query_param.mode,
                cache_type="query",
            ),
        )

    return response


# TODO: Deprecated, use user_prompt in QueryParam instead
async def kg_query_with_keywords(
    query: str,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
    global_config: dict[str, str],
    hashing_kv: BaseKVStorage | None = None,
    ll_keywords: list[str] = [],
    hl_keywords: list[str] = [],
    chunks_vdb: BaseVectorStorage | None = None,
) -> str | AsyncIterator[str]:
    """
    Refactored kg_query that does NOT extract keywords by itself.
    It expects hl_keywords and ll_keywords to be set in query_param, or defaults to empty.
    Then it uses those to build context and produce a final LLM response.
    """
    if query_param.model_func:
        use_model_func = query_param.model_func
    else:
        use_model_func = global_config["llm_model_func"]
        # Apply higher priority (5) to query relation LLM function
        use_model_func = partial(use_model_func, _priority=5)

    args_hash = compute_args_hash(query_param.mode, query)
    cached_response, quantized, min_val, max_val = await handle_cache(
        hashing_kv, args_hash, query, query_param.mode, cache_type="query"
    )
    if cached_response is not None:
        return cached_response

    # If neither has any keywords, you could handle that logic here.
    if not hl_keywords and not ll_keywords:
        logger.warning(
            "No keywords found in query_param. Could default to global mode or fail."
        )
        return PROMPTS["fail_response"]
    if not ll_keywords and query_param.mode in ["local", "hybrid"]:
        logger.warning("low_level_keywords is empty, switching to global mode.")
        query_param.mode = "global"
    if not hl_keywords and query_param.mode in ["global", "hybrid"]:
        logger.warning("high_level_keywords is empty, switching to local mode.")
        query_param.mode = "local"

    ll_keywords_str = ", ".join(ll_keywords) if ll_keywords else ""
    hl_keywords_str = ", ".join(hl_keywords) if hl_keywords else ""

    context = await _build_query_context(
        query,
        ll_keywords_str,
        hl_keywords_str,
        knowledge_graph_inst,
        entities_vdb,
        relationships_vdb,
        text_chunks_db,
        query_param,
        chunks_vdb=chunks_vdb,
    )
    if not context:
        return PROMPTS["fail_response"]

    if query_param.only_need_context:
        return context

    # Process conversation history
    history_context = ""
    if query_param.conversation_history:
        history_context = get_conversation_turns(
            query_param.conversation_history, query_param.history_turns
        )

    sys_prompt_temp = PROMPTS["rag_response"]
    sys_prompt = sys_prompt_temp.format(
        context_data=context,
        response_type=query_param.response_type,
        history=history_context,
    )

    if query_param.only_need_prompt:
        return sys_prompt

    tokenizer: Tokenizer = global_config["tokenizer"]
    len_of_prompts = len(tokenizer.encode(query + sys_prompt))
    logger.debug(f"[kg_query_with_keywords]Prompt Tokens: {len_of_prompts}")

    # 6. Generate response
    response = await use_model_func(
        query,
        system_prompt=sys_prompt,
        stream=query_param.stream,
    )

    # Clean up response content
    if isinstance(response, str) and len(response) > len(sys_prompt):
        response = (
            response.replace(sys_prompt, "")
            .replace("user", "")
            .replace("model", "")
            .replace(query, "")
            .replace("<system>", "")
            .replace("</system>", "")
            .strip()
        )

        if hashing_kv.global_config.get("enable_llm_cache"):
            await save_to_cache(
                hashing_kv,
                CacheData(
                    args_hash=args_hash,
                    content=response,
                    prompt=query,
                    quantized=quantized,
                    min_val=min_val,
                    max_val=max_val,
                    mode=query_param.mode,
                    cache_type="query",
                ),
            )

    return response


# TODO: Deprecated, use user_prompt in QueryParam instead
async def query_with_keywords(
    query: str,
    prompt: str,
    param: QueryParam,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    chunks_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    global_config: dict[str, str],
    hashing_kv: BaseKVStorage | None = None,
) -> str | AsyncIterator[str]:
    """
    Extract keywords from the query and then use them for retrieving information.

    1. Extracts high-level and low-level keywords from the query
    2. Formats the query with the extracted keywords and prompt
    3. Uses the appropriate query method based on param.mode

    Args:
        query: The user's query
        prompt: Additional prompt to prepend to the query
        param: Query parameters
        knowledge_graph_inst: Knowledge graph storage
        entities_vdb: Entities vector database
        relationships_vdb: Relationships vector database
        chunks_vdb: Document chunks vector database
        text_chunks_db: Text chunks storage
        global_config: Global configuration
        hashing_kv: Cache storage

    Returns:
        Query response or async iterator
    """
    # Extract keywords
    hl_keywords, ll_keywords = await get_keywords_from_query(
        query=query,
        query_param=param,
        global_config=global_config,
        hashing_kv=hashing_kv,
    )

    # Create a new string with the prompt and the keywords
    keywords_str = ", ".join(ll_keywords + hl_keywords)
    formatted_question = (
        f"{prompt}\n\n### Keywords\n\n{keywords_str}\n\n### Query\n\n{query}"
    )

    # Use appropriate query method based on mode
    if param.mode in ["local", "global", "hybrid", "mix"]:
        return await kg_query_with_keywords(
            formatted_question,
            knowledge_graph_inst,
            entities_vdb,
            relationships_vdb,
            text_chunks_db,
            param,
            global_config,
            hashing_kv=hashing_kv,
            hl_keywords=hl_keywords,
            ll_keywords=ll_keywords,
            chunks_vdb=chunks_vdb,
        )
    elif param.mode == "naive":
        return await naive_query(
            formatted_question,
            chunks_vdb,
            text_chunks_db,
            param,
            global_config,
            hashing_kv=hashing_kv,
        )
    else:
        raise ValueError(f"Unknown mode {param.mode}")


# CUSTOM: Rerank hook used by fork-local process_chunks_unified (upstream wires rerank inside lightrag.utils helpers).
async def apply_rerank_if_enabled(
    query: str,
    retrieved_docs: list[dict],
    global_config: dict,
    top_k: int = None,
) -> list[dict]:
    """
    Apply reranking to retrieved documents if rerank is enabled.

    Args:
        query: The search query
        retrieved_docs: List of retrieved documents
        global_config: Global configuration containing rerank settings
        top_k: Number of top documents to return after reranking

    Returns:
        Reranked documents if rerank is enabled, otherwise original documents
    """
    if not global_config.get("enable_rerank", False) or not retrieved_docs:
        return retrieved_docs

    rerank_func = global_config.get("rerank_model_func")
    if not rerank_func:
        logger.debug(
            "Rerank is enabled but no rerank function provided, skipping rerank"
        )
        return retrieved_docs

    try:
        logger.debug(
            f"Applying rerank to {len(retrieved_docs)} documents, returning top {top_k}"
        )

        # Apply reranking - let rerank_model_func handle top_k internally
        reranked_docs = await rerank_func(
            query=query,
            documents=retrieved_docs,
            top_k=top_k,
        )
        if reranked_docs and len(reranked_docs) > 0:
            if len(reranked_docs) > top_k:
                reranked_docs = reranked_docs[:top_k]
            logger.info(
                f"Successfully reranked {len(retrieved_docs)} documents to {len(reranked_docs)}"
            )
            return reranked_docs
        else:
            logger.warning("Rerank returned empty results, using original documents")
            return retrieved_docs

    except Exception as e:
        logger.error(f"Error during reranking: {e}, using original documents")
        return retrieved_docs


# CUSTOM: Chunk pipeline hosted here with structural-aware dedupe keys (page/section/manifest), rerank,
# top-k, and token truncation — extended vs upstream utils.process_chunks_unified.
async def process_chunks_unified(
    query: str,
    chunks: list[dict],
    query_param: QueryParam,
    global_config: dict,
    source_type: str = "mixed",
) -> list[dict]:
    """
    Unified processing for text chunks: deduplication, chunk_top_k limiting, reranking, and token truncation.

    Args:
        query: Search query for reranking
        chunks: List of text chunks to process
        query_param: Query parameters containing configuration
        global_config: Global configuration dictionary
        source_type: Source type for logging ("vector", "entity", "relationship", "mixed")

    Returns:
        Processed and filtered list of text chunks
    """
    if not chunks:
        return []

    # CUSTOM STRUCTURAL CHUNKING:
    # Preserve repeated text when it comes from a different structural location.
    # A warning repeated on page 2 and page 80 should remain two chunks because
    # each occurrence has different citation value. Flat chunks still dedupe by
    # content because they do not have structural fields.
    seen_content = set()
    unique_chunks = []
    for chunk in chunks:
        content = chunk.get("content", "")
        dedupe_key = (
            content,
            chunk.get("page_start"),
            chunk.get("page_end"),
            chunk.get("section_path"),
            chunk.get("artifact_manifest_path"),
        )
        if content and dedupe_key not in seen_content:
            seen_content.add(dedupe_key)
            unique_chunks.append(chunk)

    logger.debug(
        f"Deduplication: {len(unique_chunks)} chunks (original: {len(chunks)})"
    )

    # 2. Apply reranking if enabled and query is provided
    if global_config.get("enable_rerank", False) and query and unique_chunks:
        rerank_top_k = query_param.chunk_rerank_top_k or len(unique_chunks)
        unique_chunks = await apply_rerank_if_enabled(
            query=query,
            retrieved_docs=unique_chunks,
            global_config=global_config,
            top_k=rerank_top_k,
        )
        logger.debug(f"Rerank: {len(unique_chunks)} chunks (source: {source_type})")

    # 3. Apply chunk_top_k limiting if specified
    if query_param.chunk_top_k is not None and query_param.chunk_top_k > 0:
        if len(unique_chunks) > query_param.chunk_top_k:
            unique_chunks = unique_chunks[: query_param.chunk_top_k]
            logger.debug(
                f"Chunk top-k limiting: kept {len(unique_chunks)} chunks (chunk_top_k={query_param.chunk_top_k})"
            )

    # 4. Token-based final truncation
    tokenizer = global_config.get("tokenizer")
    if tokenizer and unique_chunks:
        original_count = len(unique_chunks)
        unique_chunks = truncate_list_by_token_size(
            unique_chunks,
            key=lambda x: x.get("content", ""),
            max_token_size=query_param.max_token_for_text_unit,
            tokenizer=tokenizer,
        )
        logger.debug(
            f"Token truncation: {len(unique_chunks)} chunks from {original_count} "
            f"(max tokens: {query_param.max_token_for_text_unit}, source: {source_type})"
        )

    return unique_chunks
