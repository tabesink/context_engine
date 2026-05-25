# 13 — Incremental Implementation Plan

## Current Progress Overlay

This section records implementation progress as of the fresh-agent handoff in
`15_fresh_agent_handoff.md`.

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 1 — Canonical Models | Partially complete | Pydantic models exist for `DocumentStructure`, pages, sections, blocks, assets, Source Chunks, and structure quality. The repo uses the glossary term `SourceChunk`, not `DocumentChunk`. |
| Phase 2 — Docling Parser Adapter | Partially complete | Runtime uses `TextDoclingParser` for text/Markdown and a `DoclingParser` boundary for PDFs when Docling is installed. Asset extraction, placeholder thumbnails, and content-hash deduplication exist; robust real-PDF fixture hardening and richer table/image handling remain. |
| Phase 3 — Structure Quality Scoring | Partially complete | Deterministic `StructureQualityScorer` exists and is exposed through `GET /documents/{document_id}/structure-quality`. Scoring is still simple and should be hardened with real Docling fixtures. |
| Phase 4 — PageIndex-Style TOC Refiner | Not complete | Current `TocRefiner` validates candidate sections only. Bounded LLM extraction, TOC page detection, page offset resolution, section start validation, range assignment, logging, and report production remain. |
| Phase 5 — Merge Refiner Output | Not complete | `StructureMerger`, block assignment, and asset assignment still need implementation. |
| Phase 6 — Chunk Builder | Partially complete | `StructureAwareChunkBuilder` now builds section-aware Source Chunks, splits large sections, preserves page ranges, inherits asset IDs, and records section title/path metadata for LightRAG ingestion. Further sizing/tuning against real Docling output remains. |
| Phase 7 — LightRAG Adapter | Partially complete | `ingest_source_chunks()` exists and is used for parseable text uploads. Raw LightRAG upload fallback remains for unsupported/non-text files. Query metadata preservation and asset resolution were improved. |
| Phase 8 — Retrieval Asset Resolver | Partially complete | Asset resolver can use `metadata.source_chunk_id` or `metadata.chunk_id`. Real image extraction and real LightRAG response hardening remain. |
| Phase 9 — APIs | Partially complete | Existing document routes now expose canonical structure, structure quality, section detail, chunk detail, TOC report, assets, and thumbnails. No parallel `/domains/{domain_id}/query` route was added because ADR 0005 keeps existing upload/query contracts. |
| Phase 10 — TUI Debug Screens | Partially complete | CLI services and TUI/screen renderers cover structure quality, TOC reports, canonical structure summaries, section details, and source chunk details. Fuller navigation/actions can still be improved. |

Recommended next substantial phase: harden Phase 2 against real Docling PDF fixtures, especially table snapshots, figure captions, page snapshots, and parser-output variations. The smaller Phase 6 `StructureAwareChunkBuilder` slice is implemented and now forwards section context metadata; it should be tuned with real documents.

## Phase 1 — Canonical Models

Implement:

```text
DocumentStructure
DocumentPage
DocumentSection
DocumentBlock
DocumentAsset
DocumentChunk
StructureQuality
```

Add tests for model validation and JSON serialization.

## Phase 2 — Docling Parser Adapter

Implement:

```text
DoclingParser
DocumentStructureBuilder
AssetExtractor
ThumbnailGenerator
```

Output:

```text
document_structure.json
asset files
asset metadata rows
```

## Phase 3 — Structure Quality Scoring

Implement:

```text
StructureQualityScorer
should_run_toc_refiner
```

No LLM yet.

## Phase 4 — PageIndex-Style TOC Refiner

Implement small bounded services:

```text
TocPageDetector
TocJsonExtractor
PageOffsetResolver
SectionStartValidator
SectionRangeAssigner
TocRefiner
```

Use mocked LLM tests first.

## Phase 5 — Merge Refiner Output

Implement:

```text
StructureMerger
BlockSectionAssigner
AssetSectionAssigner
```

Goal:

```text
refined sections + original Docling blocks/assets = final DocumentStructure
```

## Phase 6 — Chunk Builder

Implement:

```text
StructureAwareChunkBuilder
```

Chunks must include:

```text
chunk_id
document_id
section_id
block_ids
page range
asset_ids
text
```

## Phase 7 — LightRAG Adapter

Implement:

```text
LightRagIngestionAdapter
LightRagQueryAdapter
```

Send chunks with metadata only.

## Phase 8 — Retrieval Asset Resolver

Implement:

```text
RetrievedSourceResolver
RetrievedAssetResolver
```

Return:

```text
answer
sources
assets
```

## Phase 9 — APIs

Add:

```text
GET /documents/{document_id}/structure
GET /documents/{document_id}/assets/{asset_id}
GET /documents/{document_id}/assets/{asset_id}/thumbnail
GET /documents/{document_id}/toc-refinement-report
POST /domains/{domain_id}/query
```

## Phase 10 — TUI Debug Screens

Add screens for:

```text
structure quality
TOC refinement report
assets
chunks
query result with assets
```

## Recommended PR Order

```text
PR 1: models + storage paths
PR 2: Docling parser adapter + assets
PR 3: structure quality scorer
PR 4: TOC refiner with mocked LLM tests
PR 5: merger + chunk builder
PR 6: LightRAG adapter updates
PR 7: retrieval asset resolver
PR 8: API endpoints
PR 9: TUI debug screens
```

## Do Not Implement in v1

```text
image embeddings
image vector database
S3/MinIO
vision captioning for every image
local semantic fallback retrieval
duplicate embedding tables
large plugin framework
complex distributed storage
```
