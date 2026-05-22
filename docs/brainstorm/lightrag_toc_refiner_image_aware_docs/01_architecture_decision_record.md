# 01 — Architecture Decision Record

## Decision

Use a single canonical document-structure pipeline that combines the strengths of Docling, PageIndex, and LightRAG without duplicating responsibilities.

```text
Original document
  -> Docling parse
  -> DocumentStructure manifest
  -> extracted assets saved to storage
  -> structure quality scoring
  -> optional PageIndex-style LLM TOC refinement
  -> final sections / blocks / chunks
  -> LightRAG ingestion with metadata references
  -> query result
  -> Context Engine resolves sources + images
```

## Why This Design

The system has three different responsibilities:

| Responsibility | Owner | Reason |
|---|---|---|
| Structure-aware parsing | Docling + Context Engine | Deterministic parsing, layout, blocks, pages, tables, figures, images |
| TOC/page-range recovery | PageIndex-style refiner | LLM-based TOC reasoning is useful when PDFs have messy or offset TOCs |
| Semantic and graph retrieval | LightRAG | Avoid duplicate embedding/vector/KG storage |

## What This Avoids

This design avoids:

```text
- two independent document navigation systems
- duplicate semantic chunks in Postgres
- duplicate embeddings outside LightRAG
- image bytes inside LightRAG
- PageIndex workspace persistence beside Context Engine persistence
- LLM-first parsing for every document
- heavy multimodal retrieval infrastructure in v1
```

## Final Ownership Boundary

### Context Engine Owns

```text
uploaded document metadata
original file location
document structure manifest
sections
blocks
chunks
tables/figures/images metadata
extracted asset files
asset thumbnails
page/section/chunk lookup
TUI/API debugging views
ingestion job state
LightRAG domain/document association
```

### LightRAG Owns

```text
semantic chunks
embeddings
vector index
entity extraction
relationship extraction
knowledge graph retrieval
LightRAG domain-local retrieval state
```

## Important Architectural Rule

LightRAG may receive metadata like this:

```json
{
  "document_id": "doc_123",
  "section_id": "sec_004",
  "chunk_id": "chunk_004_002",
  "page_start": 12,
  "page_end": 14,
  "asset_ids": ["asset_018"]
}
```

LightRAG must not receive:

```text
- image bytes
- base64 images
- full document manifests
- duplicate local database state
- binary asset files
```

## Final Recommendation

Use this shape:

```text
Docling = parser of record
PageIndex TOC logic = optional refiner
Context Engine = navigation + assets + orchestration
LightRAG = semantic retrieval + KG retrieval
```
