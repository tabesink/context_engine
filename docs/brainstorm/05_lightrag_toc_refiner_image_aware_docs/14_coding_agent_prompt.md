# 14 — Coding Agent Prompt

Use this prompt with a coding agent.

```markdown
# Task: Implement Lightweight Docling + PageIndex TOC Refiner + LightRAG Document Navigation

You are a senior Python/FastAPI engineer. Write clean, lean, low-entropy code suitable for junior developers to maintain.

## Objective

Implement a document ingestion and retrieval pipeline where:

- Docling is the parser of record.
- Images/figures/tables detected by Docling are saved to Context Engine storage.
- PageIndex-style LLM TOC indexing is implemented as an optional bounded refinement layer.
- Context Engine owns document structure, assets, navigation, and debug APIs.
- LightRAG owns semantic retrieval, embeddings, and KG retrieval.
- Chunks sent to LightRAG include lightweight metadata and `asset_ids`, not image bytes.
- Retrieval responses include relevant image URLs/thumbnails when retrieved chunks have linked assets.

## Implementation Constraints

- Do not create a second document navigation system.
- Do not store image bytes in Postgres.
- Do not store image bytes or base64 in LightRAG.
- Do not implement local semantic fallback retrieval.
- Do not duplicate embeddings outside LightRAG.
- Do not create a large plugin framework.
- Keep modules explicit and small.
- Use Pydantic models or dataclasses.
- Use deterministic parsing first.
- Use LLM TOC refinement only when structure quality requires it.
- LLM calls must be bounded, logged, and validated.

## Required Modules

```text
app/document_processing/models.py
app/document_processing/docling_parser.py
app/document_processing/structure_builder.py
app/document_processing/asset_extractor.py
app/document_processing/thumbnail_generator.py
app/document_processing/structure_quality.py
app/document_processing/refinement/toc_refiner.py
app/document_processing/refinement/toc_page_detector.py
app/document_processing/refinement/page_offset_resolver.py
app/document_processing/refinement/section_start_validator.py
app/document_processing/structure_merger.py
app/document_processing/chunk_builder.py
app/services/lightrag_adapter.py
app/services/retrieval_asset_resolver.py
```

## Required APIs

```text
POST /documents/upload
GET /documents/{document_id}/structure
GET /documents/{document_id}/assets/{asset_id}
GET /documents/{document_id}/assets/{asset_id}/thumbnail
GET /documents/{document_id}/toc-refinement-report
POST /domains/{domain_id}/query
```

## Expected Ingestion Flow

```text
upload
  -> save original
  -> Docling parse
  -> save assets
  -> build initial DocumentStructure
  -> score structure quality
  -> run TOC refiner if needed
  -> merge refined sections with Docling blocks/assets
  -> build chunks
  -> send chunks to LightRAG with asset_ids
  -> save final manifest
```

## Expected Retrieval Flow

```text
query
  -> call LightRAG
  -> get source chunk ids
  -> load local chunks/sections/assets
  -> return answer + sources + related images
```

## Testing Requirements

Add tests for:

- model serialization
- asset extraction and thumbnail generation
- structure quality scoring
- TOC refiner trigger logic
- TOC refiner acceptance/rejection with mocked LLM output
- section range assignment
- chunk asset inheritance
- retrieval asset resolver
- query response includes assets

## Final Deliverable

Produce small, readable code with explicit boundaries. Prefer simple functions and classes over clever abstractions.
```
