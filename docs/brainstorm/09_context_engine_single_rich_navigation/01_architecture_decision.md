# 01 — Architecture Decision

## Decision

Use **only the rich `DocumentStructure` layer** for local navigation.

Persist `DocumentPage` as part of the rich structure so page APIs remain simple and deterministic.

Remove optional LLM-based TOC refinement during ingestion.

## Why

The codebase currently has two overlapping local navigation systems:

```text
Old/simple local navigation
 ├── parsed_documents
 ├── navigation_indexes
 ├── DocumentParser
 ├── NavigationIndexBuilder
 ├── PageIndexAdapter
 └── NavigationRetrievalEngine

Rich document structure
 ├── DocumentStructure
 ├── DocumentPage
 ├── DocumentSection
 ├── DocumentBlock
 ├── SourceChunk
 ├── DocumentAsset
 └── DocumentProcessingRepository
```

This duplication increases entropy.

The simpler final mental model is:

```text
Backend
 └── deterministic navigation
      ├── pages
      ├── sections
      ├── blocks
      ├── chunks
      └── assets

LightRAG
 └── semantic retrieval
      ├── vectors
      ├── graph
      └── semantic answer context
```

## Non-Goals

Do not:

- Add local embeddings.
- Add local semantic fallback.
- Keep runtime fallback to `parsed_documents`.
- Keep runtime fallback to `navigation_indexes`.
- Keep optional LLM-based TOC refinement.
- Introduce Neo4j or another graph DB.
- Rewrite all ingestion logic at once.
