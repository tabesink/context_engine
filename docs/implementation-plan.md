# Multi-User Hybrid RAG Implementation Plan

This is the executable build plan for the backend-only V1. It turns the brainstorm plan into phases, task checklists, behavior tests, and acceptance gates.

## V1 Scope

Ship a FastAPI backend for 5-10 authenticated users.

Included:

- JWT authentication with `admin` and `user` roles.
- Admin-only document upload, indexing, reindexing, deletion, and index rebuild operations.
- Authenticated read/query endpoints.
- PostgreSQL for users, documents, jobs, audit/query logs, and parsed/index metadata.
- pgvector for semantic embeddings.
- Redis-backed worker for indexing jobs.
- Local filesystem document storage.
- PageIndex-style navigation retrieval.
- LightRAG-style semantic retrieval behind a local adapter boundary.
- Unified `Evidence` model, hybrid retrieval router, grounded answer composer, citations, and evaluation scripts.

Excluded from V1:

- Browser UI.
- Per-document ACLs beyond "all authenticated users may read ready documents".
- Neo4j or external graph database.
- LLM-based query router as the primary router.
- Hosted object storage.

## Build Philosophy

Use vertical TDD slices:

1. Write one behavior test through a public API or public service interface.
2. Run it red.
3. Add the smallest production code that makes it green.
4. Refactor only while green.
5. Update the phase checklist before moving on.

Tests should describe observable behavior, not implementation details.

## Phase 0: Repository Setup and Architecture Skeleton

Goal: make the project runnable before adding RAG complexity.

Tasks:

- [ ] Create Python package layout under `app/`.
- [ ] Add `pyproject.toml` with runtime and test dependencies.
- [ ] Add `.env.example`.
- [ ] Add `docker-compose.yml` for PostgreSQL, Redis, API, and worker.
- [ ] Add `app/main.py`.
- [ ] Add `app/core/config.py`, `logging.py`, `security.py`, and `errors.py`.
- [ ] Add health routes.
- [ ] Add pytest setup.
- [ ] Add a first API test for `GET /health`.

Behavior slices:

- [ ] `GET /health` returns `{"status": "ok"}` without authentication.
- [ ] App settings load from environment with safe local defaults.
- [ ] Tests run with `python -m pytest -q`.

Acceptance gate:

- [ ] API imports cleanly.
- [ ] Health test passes.
- [ ] Docker Compose defines required services.
- [ ] Junior guide explains package layout.

## Phase 1: Auth, Users, Roles, and Admin-Only Guardrails

Goal: establish security before write operations exist.

Tasks:

- [ ] Add `User` and `UserRole` domain models.
- [ ] Add SQLAlchemy user model and repository.
- [ ] Add password hashing.
- [ ] Add JWT token creation and verification.
- [ ] Add `/auth/login` and `/auth/me`.
- [ ] Add `get_current_user` dependency.
- [ ] Add `require_admin` dependency.
- [ ] Add seed admin script.
- [ ] Add one protected admin smoke endpoint.

Behavior slices:

- [ ] Seeded admin can log in and receive an access token.
- [ ] Authenticated user can call `/auth/me`.
- [ ] Normal user receives `403` from an admin-only route.
- [ ] Missing/invalid token receives `401`.

Acceptance gate:

- [ ] All write routes use `require_admin`.
- [ ] Auth tests cover admin, user, unauthenticated, and invalid-token paths.
- [ ] JWT payload contains `sub`, `email`, and `role`.

## Phase 2: Document Registry and File Upload

Goal: let admins register source documents safely.

Tasks:

- [ ] Add `Document`, `DocumentStatus`, and audit models.
- [ ] Add document table and repository.
- [ ] Add filesystem storage abstraction.
- [ ] Add admin upload endpoint.
- [ ] Add authenticated document list/detail endpoints.
- [ ] Add delete endpoint that marks documents deleted.
- [ ] Add upload audit event.

Behavior slices:

- [ ] Admin can upload `.pdf`, `.md`, and `.txt` files.
- [ ] Normal user cannot upload.
- [ ] Authenticated user can list ready documents.
- [ ] Uploaded document starts as `uploaded`.
- [ ] Deleted document is not returned in normal listings.

Acceptance gate:

- [ ] Original file is stored under configured local storage root.
- [ ] Metadata and content type are persisted.
- [ ] Read endpoints never expose deleted documents.

## Phase 3: Normalized Document Parsing Layer

Goal: parse once and feed both retrieval engines from the same model.

Tasks:

- [ ] Add `Page` and `ParsedDocument` domain models.
- [ ] Implement text parser.
- [ ] Implement Markdown parser with pseudo-pages/sections.
- [ ] Implement PDF parser.
- [ ] Store parsed page text and metadata.
- [ ] Add parser service.

Behavior slices:

- [ ] Text file parses into one or more pages.
- [ ] Markdown headings become section metadata.
- [ ] PDF parser returns page-numbered text.
- [ ] Parsed output can be saved and loaded by document ID.

Acceptance gate:

- [ ] No retrieval engine reads raw upload files directly.
- [ ] Parser failures mark the document/job failed with an actionable message.

## Phase 4: PageIndex-Style Navigation Index

Goal: provide explainable document structure and page retrieval.

Tasks:

- [ ] Add `SectionNode` model.
- [ ] Add `NavigationIndexBuilder`.
- [ ] Add `PageIndexAdapter` wrapping reference ideas.
- [ ] Store tree JSON and page references.
- [ ] Add `GET /documents/{id}/structure`.
- [ ] Add `GET /documents/{id}/pages/{page}`.
- [ ] Add `NavigationRetrievalEngine`.

Behavior slices:

- [ ] User can inspect a ready document structure.
- [ ] User can retrieve a page by number.
- [ ] Query containing page/section words routes to navigation in auto mode.
- [ ] Navigation retrieval returns `Evidence` with page and section references.

Acceptance gate:

- [ ] Navigation index is rebuilt from `ParsedDocument`, not raw files.
- [ ] Page evidence includes document ID and page range.

## Phase 5: LightRAG-Style Semantic Index

Goal: provide chunk-level semantic retrieval with a stable adapter boundary.

Tasks:

- [ ] Add chunking strategy.
- [ ] Add pgvector-backed embedding table.
- [ ] Add local embedding provider interface.
- [ ] Add `LightRAGAdapter` boundary.
- [ ] Add semantic index builder.
- [ ] Add `SemanticRetrievalEngine`.
- [ ] Convert raw semantic matches into `Evidence`.

Behavior slices:

- [ ] Parsed document chunks are indexed for semantic search.
- [ ] Semantic query returns relevant chunk evidence.
- [ ] Semantic evidence includes chunk metadata.
- [ ] Semantic-only mode calls semantic retrieval only.

Acceptance gate:

- [ ] App code depends on `LightRAGAdapter`, not reference internals.
- [ ] pgvector-backed retrieval works from the API path.

## Phase 6: Hybrid Retrieval Router

Goal: expose `semantic`, `navigation`, `hybrid`, and `auto` through one evidence API.

Tasks:

- [ ] Add `RetrievalMode`.
- [ ] Add shared `RetrievalEngine` protocol.
- [ ] Add deterministic query classifier.
- [ ] Add hybrid evidence merger.
- [ ] Add `/query/retrieve`.
- [ ] Add admin-only debug details.

Merge rules:

- Deduplicate by `(document_id, page_start, page_end, normalized_text_hash)`.
- Normalize missing scores to `0.5`.
- Prefer evidence with page/section metadata when scores are close.
- Keep at most `top_k` final evidence items.
- Preserve `source_engine` for every item.

Behavior slices:

- [ ] `mode=semantic` uses semantic engine only.
- [ ] `mode=navigation` uses navigation engine only.
- [ ] `mode=hybrid` queries both engines and deduplicates evidence.
- [ ] `mode=auto` picks deterministic mode from query words.

Acceptance gate:

- [ ] Response identifies the chosen mode and source engine per evidence item.
- [ ] Non-admin users cannot request internal debug details.

## Phase 7: Answer Composer and Citation Policy

Goal: answer only from evidence unless explicitly allowed otherwise.

Tasks:

- [ ] Add answer prompt builder.
- [ ] Add answer provider interface.
- [ ] Add deterministic local answer fallback for tests/dev.
- [ ] Add citation formatter.
- [ ] Add weak-evidence refusal.
- [ ] Add `/query/answer` and `/query`.

Behavior slices:

- [ ] Answer response contains answer text and evidence citations.
- [ ] Page evidence cites page/section when available.
- [ ] Weak evidence returns a refusal unless `allow_general_fallback=true`.
- [ ] `/query` convenience endpoint retrieves and answers.

Acceptance gate:

- [ ] Answers cite evidence IDs.
- [ ] Tests verify citation discipline through API responses.

## Phase 8: Redis-Backed Jobs and Concurrent Indexing

Goal: keep indexing out of request lifecycle and protect active indexes.

Tasks:

- [ ] Add jobs table and repository.
- [ ] Add Redis queue connection.
- [ ] Add worker entrypoint.
- [ ] Add indexing task that parses, builds navigation index, and builds semantic index.
- [ ] Add per-document indexing lock.
- [ ] Add active index version fields.
- [ ] Add job list/detail/retry endpoints.

Behavior slices:

- [ ] Upload returns quickly with a job ID.
- [ ] Worker marks job running, succeeded, or failed.
- [ ] Query uses the last ready index while reindex builds a new version.
- [ ] Failed indexing does not replace active index.

Acceptance gate:

- [ ] Indexing can run from worker.
- [ ] Admin can inspect and retry jobs.

## Phase 9: Admin Operations API and Observability

Goal: make the backend operable without a UI.

Tasks:

- [ ] Add audit logs for admin writes.
- [ ] Add query logs.
- [ ] Add indexing phase logs.
- [ ] Add metrics endpoints.
- [ ] Add slow query tracing fields.
- [ ] Add token/cost tracking hooks.

Behavior slices:

- [ ] Admin can list recent audit events.
- [ ] Admin can view job and document status summaries.
- [ ] Query log captures mode, engines, latency, and user ID.

Acceptance gate:

- [ ] Errors include actionable messages.
- [ ] Logs use stable event names.

## Phase 10: Multi-User Hardening

Goal: prepare for 5-10 real users.

Tasks:

- [ ] Add per-user rate limits.
- [ ] Add query size limits.
- [ ] Add backup script.
- [ ] Add restore script.
- [ ] Add deployment docs.
- [ ] Add concurrency tests.

Behavior slices:

- [ ] Multiple authenticated users can query concurrently.
- [ ] Admin writes do not block normal reads of ready indexes.
- [ ] Rate-limited users get `429`.

Acceptance gate:

- [ ] Backup/restore path is documented and scriptable.
- [ ] Concurrency behavior is covered by tests.

## Phase 11: Evaluation and Quality Gates

Goal: measure quality instead of assuming hybrid is better.

Tasks:

- [ ] Add a small gold QA dataset.
- [ ] Add retrieval evaluation script.
- [ ] Compare semantic, navigation, hybrid, and auto modes.
- [ ] Add citation accuracy checks.
- [ ] Add regression checks for important docs.

Behavior slices:

- [ ] Evaluation script reports recall-like retrieval matches.
- [ ] Hybrid mode is measured against semantic/navigation baselines.
- [ ] Reindexing does not silently reduce answer quality.

Acceptance gate:

- [ ] Quality gate can run locally.
- [ ] Evaluation results are documented.

