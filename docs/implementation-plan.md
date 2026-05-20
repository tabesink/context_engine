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
- Unified `Evidence` model, retrieval router, grounded answer composer, citations, and evaluation script.
- Redis-backed worker path for indexing jobs, plus inline mode for deterministic local/dev flows.
- Interactive terminal UI (`context-engine` / `context-tui`) that exercises supported backend flows through HTTP; planned-only backend surfaces remain visible as gaps rather than silent stubs.

Excluded or deferred:

- Browser UI.
- Per-document ACLs beyond "all authenticated users may read ready documents".
- Browser UI for LightRAG deployment control.
- LLM-based query router as the primary router.
- Hosted object storage.
- Alembic migrations beyond the checked-in SQL cleanup/smoke scripts.
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

- Package layout under `app/`, `cli/`, `scripts/`, and `tests/`.
- `pyproject.toml` with console scripts `context-engine` and `context-tui`, both resolving to `cli.launcher:main`.
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

Current acceptance:

- Admins can upload supported files.
- Normal users cannot upload.
- Authenticated users can list and inspect ready documents.
- Navigation processing builds page/tree data from `ParsedDocument`, not raw upload files.
- Navigation evidence includes document, page, and section context when available.

## Retrieval And Answers

Implemented:

- `RetrievalMode`: `semantic`, `navigation`, `hybrid`, and `auto`.
- `RetrievalRoutingPolicy` and `RetrievalBackend` in `app/retrieval/routing_policy.py`.
- `LocalRetrievalStrategy` and `LightRAGRetrievalStrategy` in `app/retrieval/strategies.py`.
- Shared retrieval contracts for LightRAG semantic retrieval and local navigation retrieval.
- Deterministic query classifier for legacy local navigation-only fallback paths.
- Hybrid evidence merger.
- `POST /query/retrieve`.
- `POST /query/answer`.
- `POST /query`.
- Admin-only debug details through `include_debug`.
- Deterministic citation-focused answer composer.

Current acceptance:

- `mode=semantic` uses LightRAG semantic retrieval when LightRAG is enabled.
- `mode=navigation` uses local navigation retrieval.
- `mode=hybrid` combines LightRAG semantic evidence with local navigation enrichment when available.
- Context Engine does not read or write local semantic chunks or embeddings.
- Response evidence identifies `source_engine`.
- Non-admin users do not receive internal debug details.
- Answers cite evidence IDs and refuse weak evidence unless `allow_general_fallback=true`. The current deterministic composer treats evidence as weak only when every evidence item has a numeric score below `0.2`; unscored evidence is allowed.

## Remote LightRAG Integration

Implemented:

- `LIGHTRAG_ENABLED`, `LIGHTRAG_BASE_URL`, `LIGHTRAG_API_KEY`, `LIGHTRAG_DOMAIN`, `LIGHTRAG_DOMAIN_MANIFEST`, and `LIGHTRAG_TIMEOUT_SECONDS` settings.
- `app/integrations/lightrag_domains.py` for optional domain manifest resolution.
- `app/integrations/lightrag_remote_adapter.py` for HTTP-only LightRAG access.
- Remote retrieval through `/query/data`.
- Queued LightRAG ingestion through `lightrag_ingest_document` jobs.
- Status normalization helper for `/documents/track_status/{track_id}`.
- Authenticated graph proxy routes:
  - `GET /graphs`
  - `GET /graph/label/list`
  - `GET /graph/label/popular`
  - `GET /graph/label/search`
- Contract files under `external/lightrag/contract/`.
- Mocked adapter/API tests that do not require live LightRAG.

Current behavior:

- With LightRAG enabled, `auto`, `semantic`, and `hybrid` semantic retrieval go remote and map to LightRAG `mix`; `hybrid` may add local navigation evidence.
- `navigation` stays local.
- Admin upload stores a local mirror record/file, records `semantic_engine="lightrag"`, and enqueues `lightrag_ingest_document`.
- LightRAG ingestion status is tracked through `documents.metadata.lightrag` and can be refreshed through the admin status endpoint.
- Graph routes return HTTP `400` when LightRAG is disabled.

## LightRAG Domain Deployment Control

Implemented:

- `LIGHTRAG_DEPLOY_*` settings and root `.env.example` documentation.
- `app/lightrag_deploy/` control-plane module for domain models, path resolution, manifest read/write, deterministic `domain.env` generation, compose generation, Docker Compose runner boundary, and lifecycle service.
- Per-domain LightRAG PostgreSQL database/workspace metadata and generated domain env values for `PGKVStorage`, `PGDocStatusStorage`, `PGGraphStorage`, and `PGVectorStorage`.
- Admin API routes under `/admin/lightrag/domains` implemented in `app/api/routes/lightrag_admin.py`.
- User-facing `GET /lightrag/domains` (safe field subset) on the same router module.
- Domain-aware LightRAG upload/query request plumbing through `lightrag_domain_id`.
- Terminal UI service wrapper and compact admin domain list screen.

Current behavior:

- Admin create/up/down/recreate/regenerate/remove endpoints require `LIGHTRAG_DEPLOY_ENABLED=true` (HTTP `400` when disabled).
- `GET /lightrag/domains` returns a safe field subset for any authenticated user whenever the manifest can be read (used to populate `lightrag_domain_id` selections).
- Domains are stored under `.data/lightrag/domains/<domain>/`.
- Each LightRAG domain uses a LightRAG-owned PostgreSQL database such as `lightrag_manuals`; manifests record non-secret metadata only.
- The generated compose file is `.data/lightrag/docker-compose.lightrag-domains.yml`.
- Domain removal archives by default; permanent delete requires both explicit request and config opt-in.
- Default tests use fake runners and temp directories, not live Docker or live LightRAG.

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

## Terminal Client Contract

Implemented:

- Launcher `cli/launcher.py` builds `ApiClient`, `CredentialStore`, and enters the Rich loop in `cli/tui/app.py`.
- Optional launcher flags via `cli/config.py`: `--api-base-url`, `--config-dir`, `--keyring`, `--no-keyring`; `--api-base-url` falls back to `CONTEXT_ENGINE_API_BASE_URL` or `http://127.0.0.1:8000`.
- HTTP surface wrapped by `cli/api_client.py`; call patterns grouped in `cli/services/` (auth, documents, retrieval, admin documents, jobs, LightRAG, LightRAG domains, observability, health).
- Payload shaping for queries in `cli/query_payload.py` where the TUI needs explicit JSON bodies.
- TUI framework under `cli/tui/`: `navigation.py` (screen stack), `screen.py` (`TuiScreen`, `ScreenCommand`), `session_flow.py` (startup session / login vs menu), `state.py`, `keys.py`, `styles.py`, TUI `screens/` entry points, and `renderers/` for JSON and inspect views.
- Reusable ASCII/table renderers in `cli/screens/` and `cli/renderers/` (imported by `cli/tui/screens/content.py`); optional guided flows in `cli/flows/` (for example retrieval comparison).
- Main menu routes: documents, retrieval (including answer path), LightRAG graphs/labels, admin-only LightRAG domains / jobs / observability, health/readiness, login/logout—placeholders remain for backend gaps where applicable.
- Legacy `cli/main.py`: thin delegate to the launcher kept for backwards-compatible imports (`app` callable).

Current acceptance:

- The terminal client only calls backend routes, not backend internals.
- Passwords are not persisted as plaintext; tokens are not printed by the launcher.
- The saved session warns or guides the user when the effective API base URL does not match the configured default (see credential/session flow in the TUI).
- Error responses surface structured API `detail` payloads where applicable without leaking secrets.

## Former Typer Commands (Removed)

Older docs referred to discrete `ragcli …` Typer commands. The repository no longer exposes that CLI; use the interactive TUI and the same REST API from other HTTP clients. Deep-dive command-style notes may still appear under `docs/cli_docs/` for traceability only.

## Hardening Roadmap

Add these only as scoped vertical slices:

- Alembic migrations and migration tests.
- Rate limiting and request-size controls.
- Expanded retrieval evaluation datasets and quality gates.
- Richer LightRAG ingestion/status reconciliation and database provisioning operations.
- Richer TUI forms for create/start/stop/remove domain operations beyond the compact admin list and service wrappers.
- Object storage adapter for uploaded source files.
- Document-level ACLs.

## Definition Of Done For New Work

- Behavior is covered through a public interface.
- Docs that describe the public contract are updated.
- Unsupported backend surfaces remain explicit in the UX (gap/placeholder messaging) rather than pretending success.
- Secrets are never printed in API responses or terminal client output beyond what the backend returns for debugging (and admin-only debug flags stay server-enforced).
- Tests avoid live Docker and live LightRAG unless explicitly marked external integration checks; terminal client coverage includes `tests/test_cli_launcher.py`, `tests/test_cli_services.py`, `tests/test_cli_tui.py`, `tests/test_cli_api_client.py`, `tests/test_cli_screen_renderers.py`, `tests/test_cli_query_payload.py`, `tests/test_retrieval_routing_policy.py`, and LightRAG deploy tests under `tests/test_lightrag_deploy_*.py`.
