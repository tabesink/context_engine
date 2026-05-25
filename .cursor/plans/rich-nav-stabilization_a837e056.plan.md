---
name: rich-nav-stabilization
overview: Stabilize the single rich navigation migration by making Alembic the production schema source of truth, removing remaining legacy compatibility paths, and aligning admin/CLI/tests/docs around the canonical rich-only API and `document_ingest` job.
todos:
  - id: schema-bootstrap
    content: Make Alembic the production startup/deploy schema path and remove app startup reliance on create_db_and_tables().
    status: completed
  - id: job-canonical
    content: Remove legacy LightRAG job aliases and lock retry/worker paths to canonical document_ingest.
    status: completed
  - id: toc-removal
    content: Remove remaining TOC-refiner fields, labels, schema output, and tests.
    status: completed
  - id: admin-cli-api
    content: Rename/simplify admin document actions and update CLI/TUI clients and tests.
    status: completed
  - id: dead-runtime-cleanup
    content: Delete unused old retrieval/router remnants after import checks pass.
    status: completed
  - id: docs-validation
    content: Update current docs and run targeted then full validation gates.
    status: in_progress
isProject: false
---

# Single Rich Navigation Stabilization Plan

## Verified Starting Point
The repo has already fixed several items from the review: [`/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/tables.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/tables.py) has `DocumentPageRow` and no legacy parsed/navigation rows, [`/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/repositories/document_processing.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/repositories/document_processing.py) persists and loads pages, and [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py) instantiates `RichNavigationEngine`.

The remaining stabilization work is not a broad rewrite. It should remove the last partial-migration surfaces and make startup, jobs, APIs, CLI, docs, and tests agree.

## TDD Strategy
Use vertical red-green-refactor slices, one public behavior at a time. Do not write all tests first. For each slice: add or update one failing behavior test, make the smallest production change, then refactor only while green.

Primary public behaviors to lock down:
- Fresh and existing databases reach Alembic head without relying on runtime `create_all`.
- Admin upload creates only canonical `document_ingest` jobs.
- Job retry accepts only canonical `document_ingest` jobs and uses the canonical worker path.
- Admin document actions expose `reingest`, `refresh-status`, and `delete`; stale LightRAG-specific action names are gone.
- Structure quality no longer exposes TOC-refiner decisions.
- `/retrieve` remains the only query/retrieval endpoint.

## Implementation Slices

1. **Make Alembic the production schema path**
   - Add a migration step to [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-server.sh`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-server.sh) before `scripts.seed_admin`.
   - Add the Docker path for migrations in [`/data/home/tkodippili/Desktop/localTest_context_engine/docker-compose.yml`](/data/home/tkodippili/Desktop/localTest_context_engine/docker-compose.yml), either as a one-shot `migrate` service or an API/worker startup wrapper.
   - Stop calling `create_db_and_tables()` from [`/data/home/tkodippili/Desktop/localTest_context_engine/app/main.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/main.py) in app startup. Keep it only for tests/dev helper paths where explicitly intended.
   - Update [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/seed_admin.py`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/seed_admin.py) so it assumes migrations have run, or only uses `create_db_and_tables()` in a clearly test/dev-only branch.
   - Extend [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_migrations.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_migrations.py) around baseline-to-head, `document_pages`, legacy table drops, and `lightrag_ingest_document` to `document_ingest` data migration.

2. **Remove job compatibility aliases**
   - In [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/job_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/job_service.py), remove `LEGACY_DOCUMENT_INGEST_JOB_KINDS`, `enqueue_lightrag_ingest_document()`, and `run_lightrag_ingest_job()`.
   - In [`/data/home/tkodippili/Desktop/localTest_context_engine/app/workers/tasks.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/workers/tasks.py), remove the `run_lightrag_ingest_job()` alias.
   - In [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/jobs.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/jobs.py), keep retry scoped to canonical `document_ingest`; add API coverage for retry success/failure if missing.
   - Update tests that import or assert old names, especially [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py).

3. **Finish TOC refinement removal**
   - Remove `should_run_toc_refiner` from `StructureQuality` in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/document_processing/models.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/document_processing/models.py) and from `StructureQualityResponse` in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/documents.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/documents.py).
   - Remove the hardcoded scorer output in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/document_processing/refinement.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/document_processing/refinement.py).
   - Remove `