---
name: asset-surface-hardening
overview: The codebase now has initial document-processing, asset streaming, asset enrichment, LightRAG chunk-ingest contract, and Alembic scaffolding. The next low-debt step is to harden this new surface before adding more Docling or LightRAG runtime wiring.
todos:
  - id: api-asset-test
    content: Add public API tests for authenticated asset and thumbnail streaming.
    status: completed
  - id: access-policy
    content: Introduce shared-corpus `DocumentAccessPolicy` and use it in asset/document read paths touched by this slice.
    status: completed
  - id: path-confinement
    content: Enforce asset path confinement at serving time in `DocumentAssetService`.
    status: completed
  - id: asset-enrichment
    content: Harden retrieval asset resolution around explicit `source_chunk_id` metadata with fallback behavior.
    status: completed
  - id: migration-check
    content: Verify Alembic upgrade path for document-processing tables in a focused test or command.
    status: completed
  - id: working-tree-cleanup
    content: Exclude generated `__pycache__` churn from intended changes.
    status: completed
isProject: false
---

# Asset Surface Hardening Plan

## Current State From Recheck

The working tree now includes these image-aware pieces:

- `app/document_processing/`: models, storage paths, lightweight parser pipeline, and TOC refinement helpers.
- `app/storage/tables.py`: document structure/source chunk/asset/TOC report tables.
- `app/storage/repositories/document_processing.py`: persistence for structures, source chunks, and assets.
- `app/services/document_asset_service.py`: asset file lookup for streaming.
- `app/services/retrieval_asset_resolver.py`: query evidence to asset response enrichment.
- `app/api/routes/documents.py`: asset and thumbnail streaming routes.
- `app/schemas/query.py`: `include_assets`, `include_thumbnails`, `max_assets`, and top-level `assets[]` response support.
- `app/integrations/lightrag_remote_adapter.py` and `external/lightrag/contract/openapi.yaml`: initial `/documents/ingest_chunks` extension.
- `migrations/alembic/`: Alembic baseline and document-processing revision.

## Main Tensions To Fix Before More Wiring

- Asset routes currently use `DocumentService.get_ready_or_404`, but there is still no centralized `DocumentAccessPolicy`. Access behavior is correct for shared corpus, but the rule remains scattered.
- `DocumentAssetService` trusts `DocumentAsset.storage_path` directly. Even if `DocumentStoragePaths` is safe when creating paths, serving should also enforce confinement under `STORAGE_ROOT`.
- Asset routes are not yet covered through FastAPI API tests; service tests are useful but do not prove auth/routing/file streaming behavior.
- Query asset enrichment resolves only by `Evidence.id == SourceChunk.chunk_id`; LightRAG evidence mapping does not yet preserve an explicit `source_chunk_id` metadata contract.
- Alembic exists, but the baseline is intentionally empty. We should verify migration expectations before relying on it in deployment.
- `__pycache__` files appear modified in git status and should be cleaned/ignored outside the feature work.

## Recommended Next TDD Slice

1. Add a behavior test through the document asset API:
   - Authenticated user can stream an asset for a ready document.
   - Missing/non-ready document returns not found.
   - Route never exposes raw filesystem paths.

2. Introduce `DocumentAccessPolicy` without changing behavior:
   - Shared corpus remains the rule.
   - Policy gates ready document reads for documents, pages, navigation structure, assets, source chunks, and query filters.
   - Replace scattered `del user` access placeholders only where touched by the asset route slice.

3. Harden asset file serving:
   - Resolve stored asset paths through a confinement check under `STORAGE_ROOT` or the document artifact root.
   - Return not found or a controlled error for missing/out-of-root files.
   - Keep `FileResponse` route output; do not return raw paths in JSON.

4. Add focused tests for query asset enrichment:
   - Existing evidence still works when `include_assets=false`.
   - `include_assets=true` returns top-level `assets[]` for evidence linked to a source chunk.
   - Prefer explicit `source_chunk_id` metadata when present, with `Evidence.id` fallback only for compatibility.

5. Clean migration and repository confidence:
   - Run focused Alembic upgrade checks against SQLite test DB.
   - Confirm `document_processing` tables are created by migration and repository tests still pass.

6. Cleanup working tree hygiene:
   - Remove generated `__pycache__` changes from consideration.
   - Ensure `.gitignore` or repo hygiene prevents bytecode churn from entering commits.

## Defer Until After Hardening

- Wiring `structure_process_document` worker jobs.
- Replacing/deriving navigation from `DocumentStructure`.
- Making LightRAG chunk ingestion part of runtime ingestion.
- Full Docling dependency integration.
- TUI screens for structure/assets beyond raw JSON compatibility.

## Acceptance Criteria

- Asset streaming is authenticated, confined, and tested through the public API.
- Shared-corpus access is represented by one policy object, not route-by-route convention.
- Query asset enrichment has explicit source chunk metadata behavior.
- Migrations can be run in a focused check.
- No generated bytecode files are part of intended changes.