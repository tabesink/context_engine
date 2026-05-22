# 13 — Incremental Implementation Plan

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
