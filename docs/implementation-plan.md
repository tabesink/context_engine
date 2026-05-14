# Multi-User Context Engine Implementation Plan

This document is the current implementation-oriented plan for the backend-only Context Engine. It records what exists, how new work should be added, and which areas remain hardening/backlog.

For a point-in-time status summary, see `docs/implementation-status.md`.

## Current V1 Scope

The repository implements a FastAPI backend for a small authenticated user group.

Included:

- JWT authentication with `admin` and `user` roles.
- Admin-only document upload, indexing, reindexing, deletion, and index inspection.
- Authenticated document read/query endpoints.
- Local file storage for uploaded source documents.
- SQLAlchemy persistence for users, documents, jobs, logs, parsed document data, and index metadata.
- Local parser/indexing pipeline for text, Markdown, and PDF documents.
- Local navigation retrieval for page/section-oriented questions.
- Local semantic retrieval with deterministic hashed embeddings for development and tests.
- Optional remote LightRAG retrieval, upload forwarding, and graph proxy routes through HTTP.
- Unified `Evidence` model, retrieval router, grounded answer composer, citations, and evaluation script.
- Redis-backed worker path for indexing jobs, plus inline mode for deterministic local/dev flows.
- Typer `ragcli` that mirrors supported backend routes and returns explicit errors for unsupported planned surfaces.

Excluded or deferred:

- Browser UI.
- Per-document ACLs beyond "all authenticated users may read ready documents".
- In-repo LightRAG deployment orchestration.
- LLM-based query router as the primary router.
- Hosted object storage.
- Alembic migrations.
- Production embedding provider and real pgvector column/type usage.
- Rate limiting.

## Build Philosophy

Use vertical behavior slices:

1. Write one behavior test through a public API, CLI command, adapter, or public service interface.
2. Run it red.
3. Add the smallest production code that makes it green.
4. Refactor only while green.
5. Update the relevant documentation before moving on.

Tests should describe observable behavior, not private implementation details.

## Implemented Foundation

The runnable foundation includes:

- Package layout under `app/`, `cli/`, `scripts/`, and `tests/`.
- `pyproject.toml` with the `ragcli = "cli.main:app"` console script.
- `.env.example`.
- `docker-compose.yml` with PostgreSQL, Redis, API, and worker services.
- `app/main.py` app factory and route registration.
- `app/core/config.py`, logging, security, and error helpers.
- Health routes.
- Pytest setup and behavior tests.

Current acceptance:

- API imports cleanly.
- Health routes are public.
- App settings load from environment with safe local defaults.
- Compose defines the app database, Redis, API, and worker services.

## Auth, Users, Roles, And Guardrails

Implemented:

- User and role models.
- SQLAlchemy user table and repository.
- Password hashing.
- JWT token creation and verification.
- `/auth/login` and `/auth/me`.
- `get_current_user` dependency.
- `require_admin` dependency.
- Seed admin script.

Current acceptance:

- Seeded admin can log in and receive an access token.
- Authenticated users can call `/auth/me`.
- Normal users receive `403` from admin-only routes.
- Missing or invalid tokens receive auth errors.
- Write routes use backend authorization rather than CLI-side permission inference.

## Documents, Parsing, And Local Indexing

Implemented:

- Document domain/storage models.
- Filesystem upload storage.
- Admin upload endpoint.
- Authenticated document list/detail endpoints.
- Soft delete path.
- Text, Markdown, and PDF parsing.
- Parsed page/section persistence.
- Navigation index builder.
- PageIndex-style adapter.
- Structure and page endpoints.
- Local semantic chunking and deterministic embedding generation.

Current acceptance:

- Admins can upload supported files.
- Normal users cannot upload.
- Authenticated users can list and inspect ready documents.
- Local indexing builds navigation and semantic data from `ParsedDocument`, not raw upload files.
- Navigation evidence includes document, page, and section context when available.

## Retrieval And Answers

Implemented:

- `RetrievalMode`: `semantic`, `navigation`, `hybrid`, and `auto`.
- Shared local `RetrievalEngine` contract.
- Deterministic query classifier for local `auto`.
- Hybrid evidence merger.
- `POST /query/retrieve`.
- `POST /query/answer`.
- `POST /query`.
- Admin-only debug details through `include_debug`.
- Deterministic citation-focused answer composer.

Current acceptance:

- `mode=semantic` uses local semantic retrieval when LightRAG is disabled.
- `mode=navigation` uses local navigation retrieval.
- `mode=hybrid` merges local semantic and navigation evidence when LightRAG is disabled.
- `mode=auto` selects the local route deterministically when LightRAG is disabled.
- Response evidence identifies `source_engine`.
- Non-admin users do not receive internal debug details.
- Answers cite evidence IDs and refuse weak evidence unless `allow_general_fallback=true`. The current deterministic composer treats evidence as weak only when every evidence item has a numeric score below `0.2`; unscored evidence is allowed.

## Remote LightRAG Integration

Implemented:

- `LIGHTRAG_ENABLED`, `LIGHTRAG_BASE_URL`, `LIGHTRAG_API_KEY`, `LIGHTRAG_DOMAIN`, `LIGHTRAG_DOMAIN_MANIFEST`, and `LIGHTRAG_TIMEOUT_SECONDS` settings.
- `app/integrations/lightrag_domains.py` for optional domain manifest resolution.
- `app/integrations/lightrag_remote_adapter.py` for HTTP-only LightRAG access.
- Remote retrieval through `/query/data`.
- Multipart upload forwarding through `/documents/upload`.
- Status normalization helper for `/documents/track_status/{track_id}`.
- Authenticated graph proxy routes:
  - `GET /graphs`
  - `GET /graph/label/list`
  - `GET /graph/label/popular`
  - `GET /graph/label/search`
- Contract files under `external/lightrag/contract/`.
- Mocked adapter/API tests that do not require live LightRAG.

Current behavior:

- `LIGHTRAG_ENABLED=false` keeps the local path active.
- With LightRAG enabled, `auto`, `semantic`, and `hybrid` retrieval go remote and map to LightRAG `mix`.
- With LightRAG enabled, `navigation` stays local.
- Admin upload stores a local mirror record/file and forwards the file to LightRAG.
- LightRAG upload responses may return `job_id: null`; remote ingestion status is tracked through LightRAG metadata.
- Graph routes return a disabled-service error when LightRAG is disabled.

## Jobs, Worker, And Operations

Implemented:

- Job table and repository.
- Redis `rq` enqueue path.
- Worker entrypoint.
- Indexing task that parses and builds local indexes.
- Job list/detail/retry endpoints.
- Audit logs and query logs.
- Admin audit/query log CLI commands.
- Backup and retrieval evaluation scripts.

Current acceptance:

- Upload returns quickly with a job ID in the local indexing path.
- Worker-owned jobs move through queued/running/succeeded/failed states.
- Failed indexing does not replace ready data.
- Admins can inspect and retry jobs.
- Errors include actionable messages.
- Logs use stable enough event data for tests and operator inspection.

## CLI Contract

Implemented:

- `ragcli login`, `logout`, and `auth me`.
- `ragcli documents list/show/structure/page/retrieve/answer`.
- `ragcli query`.
- `ragcli admin documents upload/list/index/reindex/delete`.
- `ragcli admin audit-logs list`.
- `ragcli admin query-logs list`.
- `ragcli jobs list/status/retry`.
- `ragcli lightrag graphs show`.
- `ragcli lightrag labels list/popular/search`.
- Planned command groups that return `not_supported_by_backend`.

Current acceptance:

- CLI commands call backend routes, not backend internals.
- Passwords are not stored.
- Access tokens are not printed.
- Authenticated commands use the saved login base URL and warn when the current `--api-base-url` differs.
- JSON errors use a structured `error` object.

## Hardening Roadmap

Add these only as scoped vertical slices:

- Alembic migrations and migration tests.
- Production-grade embedding provider and pgvector-backed semantic search.
- Rate limiting and request-size controls.
- Expanded retrieval evaluation datasets and quality gates.
- Better LightRAG ingestion/status reconciliation.
- Backend admin APIs for LightRAG domain/deployment management, if deployment orchestration becomes a product requirement.
- Object storage adapter for uploaded source files.
- Document-level ACLs.

## Definition Of Done For New Work

- Behavior is covered through a public interface.
- Docs that describe the public contract are updated.
- Unsupported CLI/backend surfaces fail explicitly instead of pretending success.
- Secrets are never printed in API or CLI output.
- Tests do not require live Docker or live LightRAG unless the test is explicitly marked as an external integration check.
