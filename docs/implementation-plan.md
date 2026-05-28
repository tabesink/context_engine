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
- LightRAG-only semantic retrieval, queued LightRAG ingestion, graph proxy routes, and admin-controlled domain deployment through generated `.data/lightrag` files.
- Unified `Evidence` model, retrieval router, and evaluation script.
- Redis-backed worker path for indexing jobs, plus inline mode for deterministic local/dev flows.
- Legacy terminal UI (`context-engine`) remains in-repo for transition/testing continuity but is deprecated and not a supported workflow.

Excluded or deferred:

- Browser UI.
- Per-document ACLs beyond "all authenticated users may read ready documents".
- Browser UI for LightRAG deployment control.
- LLM-based query router as the primary router.
- Hosted object storage.
- Migration hardening beyond the Alembic baseline and feature revisions.
- Per-domain credential rotation and richer database provisioning operations.
- Rate limiting.

## Build Philosophy

Use vertical behavior slices:

1. Write one behavior test through a public API, launcher/TUI-facing test harness, adapter, or public service interface.
2. Run it red.
3. Add the smallest production code that makes it green.
4. Refactor only while green.
5. Update the relevant documentation before moving on.

Tests should describe observable behavior, not private implementation details.

## Implemented Foundation

The runnable foundation includes:

- Package layout under `app/`, `scripts/`, and `tests/` (legacy deprecated CLI/TUI code remains under `cli/`).
- `pyproject.toml` with console script `context-engine` resolving to `cli.launcher:main`.
- `.env.example`.
- `docker-compose.yml` with PostgreSQL, Redis, API, worker, and shared-network support for generated LightRAG domain services.
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

## Documents, Parsing, And Navigation

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
- Docling parser normalization for label variants and provenance fallback, plus detached-caption propagation to image/table asset metadata when item-level captions are missing.

Current acceptance:

- Admins can upload supported files.
- Normal users cannot upload.
- Authenticated users can list and inspect ready documents.
- Navigation processing builds page/tree data from `ParsedDocument`, not raw upload files.
- Navigation evidence includes document, page, and section context when available.

## Retrieval

Implemented:

- `RetrievalMode`: `semantic`, `navigation`, `hybrid`, and `auto`.
- `RetrievalRoutingPolicy` and `RetrievalBackend` in `app/retrieval/routing_policy.py`.
- `LocalRetrievalStrategy` and `LightRAGRetrievalStrategy` in `app/retrieval/strategies.py`.
- Shared retrieval contracts for mandatory LightRAG semantic retrieval and local navigation retrieval.
- Hybrid evidence merger.
- `POST /retrieve`.
- Admin-only debug details through `include_debug`.

Current acceptance:

- `mode=semantic` always uses LightRAG semantic retrieval.
- `mode=navigation` uses local navigation retrieval.
- `mode=hybrid` combines LightRAG semantic evidence with local navigation enrichment.
- `mode=auto` routes to LightRAG semantic retrieval.
- Context Engine does not read or write local semantic chunks or embeddings.
- Response evidence identifies `source_engine`.
- Non-admin users do not receive internal debug details.

## Remote LightRAG Integration

Implemented:

- `LIGHTRAG_DOMAIN_REGISTRY` and `LIGHTRAG_TIMEOUT_SECONDS` settings. Remote LightRAG is required; there is no local semantic fallback flag.
- `app/services/lightrag_domain_registry.py` for mandatory registered-domain resolution.
- `app/integrations/lightrag_remote_adapter.py` for HTTP-only LightRAG access.
- Remote retrieval through `/query/data`.
- Queued LightRAG ingestion through `document_ingest` jobs.
- Status normalization helper for `/documents/track_status/{track_id}`.
- Normalized processing-status APIs and service-level aggregation:
  - `GET /lightrag/domains/{domain_id}/processing-status`
  - `GET /admin/lightrag/domains/{domain_id}/processing-status`
  - `GET /documents/{document_id}/processing-status`
  - `GET /admin/documents/{document_id}/processing-status`
  - `ProcessingStatusService` joins local docs/jobs with remote `pipeline_status` + `status_counts` and applies user/admin projections.
- Authenticated graph proxy routes:
  - `GET /lightrag/domains/{domain_id}/graphs`
  - `GET /lightrag/domains/{domain_id}/graph/labels`
  - `GET /lightrag/domains/{domain_id}/graph/labels/popular`
  - `GET /lightrag/domains/{domain_id}/graph/labels/search`
- Contract files under `external/lightrag/contract/`.
- Mocked adapter/API tests that do not require live LightRAG.

Current behavior:

- With LightRAG enabled, `auto`, `semantic`, and `hybrid` semantic retrieval go remote and map to LightRAG `mix`; `hybrid` may add local navigation evidence.
- `navigation` stays local.
- Admin upload stores a local mirror record/file, records LightRAG metadata, and enqueues `document_ingest`.
- LightRAG ingestion status is tracked through `documents.metadata.lightrag` and can be refreshed through the admin status endpoint.
- Processing status polling is backend-coalesced with short TTL caching to reduce upstream LightRAG fanout.
- Graph routes return HTTP `400` when LightRAG is disabled.

## LightRAG Domain Deployment Control

Implemented:

- `LIGHTRAG_DEPLOY_*` settings and root `.env.example` documentation.
- Provider passthrough settings for generated LightRAG runtime env files:
  - Root config keys: `LIGHTRAG_LLM_*`, `LIGHTRAG_KEYWORD_LLM_MODEL`, `LIGHTRAG_QUERY_LLM_MODEL`, `LIGHTRAG_VLM_LLM_MODEL`, `LIGHTRAG_EMBEDDING_*`, and `LIGHTRAG_OPENAI_LLM_*`.
  - Generated domain keys: `LLM_BINDING*`, `EMBEDDING_BINDING*`, and `OPENAI_LLM_*`.
- `app/lightrag_deploy/` control-plane module for domain models, path resolution, manifest read/write, deterministic `domain.env` generation, compose generation, Docker Compose runner boundary, and lifecycle service.
- Per-domain LightRAG PostgreSQL database/workspace metadata and generated domain env values for `PGKVStorage`, `PGDocStatusStorage`, `PGGraphStorage`, and `PGVectorStorage`.
- Admin API routes under `/admin/lightrag/domains` implemented in `app/api/routes/lightrag_admin.py`.
- User-facing `GET /lightrag/domains` (safe field subset) on the same router module.
- Domain-aware LightRAG upload/query request plumbing through `lightrag_domain_id`.
- Terminal UI service wrapper and compact admin domain list screen.

Current behavior:

- Admin create/up/down/repair/remove/purge-preview/purge endpoints require admin auth; deploy settings are validated at startup.
- Advanced compatibility endpoints (`recreate`, `regenerate`) remain available but are not part of the normal admin lifecycle workflow.
- `GET /lightrag/domains` returns a safe field subset for any authenticated user whenever the manifest can be read (used to populate `lightrag_domain_id` selections).
- Domains are stored under `.data/lightrag/domains/<domain>/`.
- Each LightRAG domain uses a LightRAG-owned PostgreSQL database such as `lightrag_manuals`; manifests record non-secret metadata only.
- Provider API keys are intentionally scoped to per-domain `domain.env` only; compose and manifest artifacts remain secret-free.
- The generated compose file is `.data/lightrag/docker-compose.lightrag-domains.yml`.
- Domain removal archives by default.
- Permanent deletion must use `purge-preview` followed by `purge` (with confirm-domain-id and config opt-in).
- `DELETE /admin/lightrag/domains/{id}?permanent=true` is deprecated and rejected with migration guidance.
- Default tests use fake runners and temp directories, not live Docker or live LightRAG.
- Bedrock OpenAI-compatible deployments are supported by keeping `LIGHTRAG_LLM_BINDING=openai` and targeting a Bedrock OpenAI-compatible host URL (`.../openai/v1`) instead of switching to a native Bedrock binding.

## Jobs, Worker, And Operations

Implemented:

- Job table and repository.
- Redis `rq` enqueue path.
- Worker entrypoint.
- Navigation processing task that parses and builds local page/tree indexes.
- LightRAG ingestion task that serializes same-domain uploads with a Redis lock, uploads to LightRAG, and updates local LightRAG status metadata.
- Job list/detail/retry endpoints.
- Audit/query log repositories, admin-facing log endpoints, and read-only observability in the terminal UI.
- Backup and retrieval evaluation scripts.

Current acceptance:

- Upload returns quickly with a job ID for LightRAG ingestion and may also queue navigation processing.
- Worker-owned jobs move through queued/running/succeeded/failed states.
- Failed indexing does not replace ready data.
- Admins can inspect and retry jobs.
- Errors include actionable messages.
- Logs use stable enough event data for tests and operator inspection.

## Terminal Client Contract (Deprecated)

Legacy implementation (deprecated, unsupported for active workflows):

- Launcher `cli/launcher.py` builds `ApiClient`, `CredentialStore`, and enters the Rich loop in `cli/tui/app.py`.
- Optional launcher flags via `cli/config.py`: `--api-base-url`, `--config-dir`, `--keyring`, `--no-keyring`; `--api-base-url` falls back to `CONTEXT_ENGINE_API_BASE_URL` or `http://127.0.0.1:8000`.
- HTTP surface wrapped by `cli/api_client.py`; call patterns grouped in `cli/services/` (auth, documents, retrieval, admin documents, jobs, LightRAG, LightRAG domains, observability, health).
- Payload shaping for retrieval in `cli/retrieve_payload.py` where the TUI needs explicit JSON bodies.
- TUI framework under `cli/tui/`: `navigation.py` (screen stack), `screen.py` (`TuiScreen`, `ScreenCommand`), `session_flow.py` (startup session / login vs menu), `state.py`, `keys.py`, `styles.py`, TUI `screens/` entry points, and `renderers/` for JSON and inspect views.
- Reusable ASCII/table renderers in `cli/screens/` and `cli/renderers/` (imported by `cli/tui/screens/content.py`); optional guided flows in `cli/flows/` (for example retrieval comparison).
- Main menu routes: documents, retrieval, LightRAG graphs/labels, admin-only LightRAG domains / jobs / observability, health/readiness, login/logout—placeholders remain for backend gaps where applicable.
- Legacy `cli/main.py`: thin delegate to the launcher kept for backwards-compatible imports (`app` callable).

Current legacy behavior:

- The terminal client only calls backend routes, not backend internals.
- Passwords are not persisted as plaintext; tokens are not printed by the launcher.
- The saved session warns or guides the user when the effective API base URL does not match the configured default (see credential/session flow in the TUI).
- Error responses surface structured API `detail` payloads where applicable without leaking secrets.

## Former Typer Commands (Removed)

Older docs referred to discrete `ragcli …` Typer commands. The repository no longer exposes that CLI; use the REST API from supported clients. Deep-dive command-style notes may still appear under `docs/cli_docs/` for traceability only.

## Hardening Roadmap

Add these only as scoped vertical slices:

- Migration hardening beyond the Alembic baseline and feature revisions.
- Rate limiting and request-size controls.
- Expanded retrieval evaluation datasets and quality gates.
- Richer LightRAG ingestion/status reconciliation and database provisioning operations.
- Domain deployment UX hardening through supported API/web surfaces (legacy TUI forms are out of scope).
- Object storage adapter for uploaded source files.
- Document-level ACLs.

## Definition Of Done For New Work

- Behavior is covered through a public interface.
- Docs that describe the public contract are updated.
- Unsupported backend surfaces remain explicit in the UX (gap/placeholder messaging) rather than pretending success.
- Secrets are never printed in API responses or terminal client output beyond what the backend returns for debugging (and admin-only debug flags stay server-enforced).
- Tests avoid live Docker and live LightRAG unless explicitly marked external integration checks; legacy CLI/TUI coverage remains for transitional stability (`tests/test_cli_*`), alongside active API/retrieval/deploy coverage such as `tests/test_retrieval_routing_policy.py` and `tests/test_lightrag_deploy_*.py`.
