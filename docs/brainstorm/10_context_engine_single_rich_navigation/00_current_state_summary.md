# 00 — Current State Summary

## Goal of This Pass

Rerun the entropy-reduction review against the updated repo and turn it into an implementation plan.

## High-Level Diagnosis

The updated repo has completed the core single-rich-navigation migration and is now in final cleanup/hardening.

```text
Current state:

1. Rich local navigation is the runtime source of truth
   ├── DocumentPageRow/DocumentSectionRow/DocumentBlockRow/DocumentSourceChunkRow/DocumentAssetRow
   ├── DocumentProcessingRepository persists and reads full rich structure
   └── page + structure APIs read rich storage

2. Retrieval runtime is fully wired to rich navigation + LightRAG
   ├── navigation mode uses RichNavigationEngine
   ├── semantic mode uses LightRAG only
   └── hybrid mode combines LightRAG and rich navigation evidence

3. Legacy runtime paths are removed
   ├── parsed_documents/navigation_indexes tables removed
   ├── NavigationRetrievalEngine/PageIndexAdapter removed
   └── TOC refinement runtime/API paths removed
```

## Main Architectural Problem

The system currently has too many ways to represent local navigation:

```text
Old model:
  parsed page JSON + navigation index tree

New model:
  DocumentStructure.pages/sections/blocks/source_chunks/assets

Semantic model:
  LightRAG remote chunks/vector/graph state
```

The cleanup should leave only:

```text
Local deterministic navigation:
  DocumentStructure

Semantic retrieval:
  LightRAG
```

## Most Important Stabilization Items

```text
[x] Add/verify `DocumentPageRow`.
[x] Add/verify `DocumentPage.metadata`.
[x] Ensure `DocumentProcessingRepository` imports cleanly.
[x] Ensure rich page save/load works.
[x] Route `GET /documents/{id}/pages/{n}` to rich pages.
[x] Route `mode=navigation` to `RichNavigationEngine`.
[x] Remove structure fallback to old navigation index.
[x] Remove TOC refinement.
[ ] Canonicalize job kind to `document_ingest` (with legacy compatibility).
[ ] Remove stale CLI/TUI calls to removed TOC/index/reindex endpoints.
[ ] Keep full LightRAG domain deployment lifecycle (`/admin/lightrag/domains/*`) and guard with tests.
```

## Do Not Start With

Do not remove the LightRAG deploy control plane. This project keeps in-app domain lifecycle operations.

Avoid:

```text
Deleting old tables before migration/backfill.
Deleting old services before APIs no longer call them.
Changing route names before the current route behavior is stable.
```
