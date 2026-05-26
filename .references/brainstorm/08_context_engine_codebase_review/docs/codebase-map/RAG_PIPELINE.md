# RAG Pipeline

## Pipeline Summary

The system is a hybrid RAG backend with two complementary retrieval paths:

1. Remote LightRAG semantic retrieval
2. Local structured document navigation retrieval

Recommended conceptual flow:

```text
source document
  → upload
  → parse/extract
  → normalized document structure
  → local pages/sections/chunks/assets
  → LightRAG ingestion
  → retrieval request
  → semantic retrieval and/or navigation retrieval
  → evidence/citation response
```

## Ingestion Flow

```text
admin uploads file
  → API validates admin
  → DocumentService stores original file
  → document metadata row is created
  → processing job is queued
  → worker parses document
  → pages/sections/chunks/assets are stored locally
  → content is sent to LightRAG domain
  → processing status is updated
```

## Local Structured Model

The local model should preserve:

- document identity
- page numbers
- section hierarchy
- chunk text
- chunk-to-page mapping
- chunk-to-section mapping
- assets such as images/tables
- source path/title metadata

This enables frontend features such as:

- workspace tree
- document outline
- page navigation
- right-side evidence panel
- citations that link to document/page/chunk
- image/table evidence cards

## Semantic Retrieval

Remote LightRAG should handle:

- semantic/vector retrieval
- graph retrieval
- hybrid graph-vector retrieval
- LightRAG-specific storage
- LightRAG provider/model behavior

The backend should treat LightRAG as an external service.

Internal code should communicate through:

```text
LightRAGRemoteAdapter
```

or equivalent.

## Navigation Retrieval

Local navigation retrieval should handle:

- document title matching
- section/page/chunk keyword lookup
- asset lookup
- workspace/tree navigation
- known document/page/section references
- exact-ish local evidence discovery

Important naming rule:

Call this **navigation retrieval** or **structured lookup**, not full semantic search.

## Hybrid Retrieval

Hybrid retrieval should:

```text
semantic evidence from LightRAG
  + local navigation evidence
  → normalize
  → deduplicate
  → rank/merge
  → enrich with local metadata/assets
  → return stable evidence objects
```

## Evidence Object

Recommended stable evidence fields:

```json
{
  "reference_id": "E1",
  "source_path": "uploads/file.pdf",
  "document_id": "doc_123",
  "document_title": "Document title",
  "chunk_id": "chunk_456",
  "section_id": "section_789",
  "page_number": 12,
  "score": 0.82,
  "text": "Evidence text",
  "asset_ids": ["asset_1"],
  "assets": [
    {
      "asset_id": "asset_1",
      "type": "image",
      "url": "/documents/doc_123/assets/asset_1",
      "caption": "Figure 2"
    }
  ],
  "metadata": {}
}
```

## Asset Enrichment

When evidence maps to a chunk/page/section, the backend should be able to attach relevant assets:

```text
evidence chunk
  → local chunk_id/page_number
  → nearby assets/images/tables
  → compact asset metadata
  → frontend renders evidence card
```

Asset enrichment should be optional because it may increase response size.

## Frontend Evidence Panel Support

Recommended compact citation map:

```text
[E1] Document Title · p. 12 · Section 3.2
     Evidence snippet...
     Assets: Figure, Table

[E2] Another Document · p. 4
     Evidence snippet...
```

The frontend should not need to understand LightRAG internals.

## Retrieval Access Policy

Recommended new boundary:

```text
RetrievalAccessPolicy
```

Responsibilities:

- resolve visible domains
- resolve allowed documents
- enforce shared-corpus or future tenant policy
- filter requested document IDs
- prevent retrieval engines from handling authorization

V1 behavior may be:

```text
All authenticated users can read all READY documents in visible shared domains.
Only admins can write.
```

But this must be documented as intentional.

## RAG Evaluation and Debugging

Future recommended additions:

- retrieval debug mode
- query route/mode logging
- evidence score logging
- LightRAG response timing
- provider latency/cost logging
- small evaluation dataset
- regression tests for known queries
- admin-only retrieval trace endpoint
