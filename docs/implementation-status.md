# Implementation Status

This file records what the current codebase implements. For the intended build sequence and maintenance roadmap, see `docs/implementation-plan.md`.

## Implemented

- FastAPI app factory, route registration, health endpoints, and startup table creation.
- SQLAlchemy storage models and repositories for users, documents, jobs, parsed/index data, audit logs, and query logs.
- JWT auth, password hashing, `/auth/login`, `/auth/me`, `get_current_user`, and `require_admin`.
- Admin document upload, index, reindex, delete, and list endpoints.
- Authenticated document list, detail, structure, and page endpoints.
- Text, Markdown, and PDF parsing into normalized parsed-document data.
- Navigation index builder and PageIndex-style navigation adapter.
- LightRAG-only semantic retrieval; local semantic chunks and deterministic embedding fallback have been removed from runtime code.
- Retrieval router with `semantic`, `navigation`, `hybrid`, and `auto` modes; `RetrievalRoutingPolicy` selects local navigation versus LightRAG-backed retrieval; `LightRAGRetrievalStrategy` can combine LightRAG evidence with local navigation evidence for hybrid mode.
- Evidence-only retrieval via `POST /query/retrieve`.
- Answer composition via `POST /query/answer` and `POST /query`.
- Admin-only debug details when `include_debug=true`.
- Job table, job status endpoints, Redis `rq` enqueue path, and worker-owned job lifecycle.
- Audit/query log repositories and admin log endpoints.
- Seed admin, backup, and retrieval evaluation scripts.
- Interactive terminal UI: console scripts `context-engine` / `context-tui` (`cli.launcher`) driving `cli/tui/app.py` plus `cli/tui/` navigation, screens, and helpers; `cli/screens/` + `cli/renderers/` supply composable layouts; `cli/flows/` holds multi-step UX; all HTTP via `ApiClient` and `cli/services/`.
- Remote LightRAG integration behind `LIGHTRAG_ENABLED`, including HTTP adapter, domain manifest resolution, retrieval strategy, queued ingestion jobs, status refresh, and graph proxy routes.
- LightRAG domain deployment control behind `LIGHTRAG_DEPLOY_ENABLED`, including managed domain manifest, generated domain env files, generated compose file, fakeable Docker Compose runner, admin APIs in `app/api/routes/lightrag_admin.py`, user-safe `GET /lightrag/domains`, domain-aware upload/query selection, per-domain PostgreSQL storage metadata, and matching TUI/admin service wrappers.
- Contract files under `external/lightrag/contract/`.
- Behavior tests for API, terminal client (launcher, settings, TUI, services, API client, screen renderers, query payload), routing policy, LightRAG adapter, LightRAG deploy stack, auth guardrails, upload, retrieval, answer flow, queued jobs, and worker failure handling.

## LightRAG Runtime Behavior

`LIGHTRAG_ENABLED=true` is the expected integration runtime. Tests may inject/fake the remote adapter boundary, but runtime semantic retrieval has no local fallback.

When `LIGHTRAG_ENABLED=true`:

- `auto`, `semantic`, and `hybrid` semantic retrieval use `LightRAGRemoteRetrievalEngine` and `LightRAGRemoteAdapter`; `hybrid` can add local navigation evidence.
- `navigation` retrieval remains local.
- Admin upload stores a local mirror record/file and enqueues `lightrag_ingest_document`.
- Upload responses include the LightRAG ingestion job id; LightRAG status is tracked under `documents.metadata.lightrag`.
- `GET /graphs` and `GET /graph/label/...` proxy to the remote LightRAG service; when LightRAG integration is off, these routes return HTTP `400` (`LightRAG is disabled`).
- LightRAG timeouts/connect failures become `503`; auth/upstream/invalid-response failures become `502`.

## Intentional Simplifications

- Startup table creation is used instead of Alembic migrations.
- SQL cleanup/smoke scripts live under `migrations/`; they are not yet an Alembic migration chain.
- Context Engine stores LightRAG metadata and navigation data only; LightRAG owns chunks, embeddings, vector indexes, and graph data.
- The answer composer is deterministic and citation-focused. A real LLM provider can be added behind the same composer/provider boundary.
- Document ACLs are deferred; authenticated users can read ready documents.
- LightRAG domain deployment control is opt-in and generates a separate `.data/lightrag/docker-compose.lightrag-domains.yml`; generated domain services share the root Docker network.

## Next Hardening Items

- Add Alembic migrations.
- Add rate limiting middleware and stronger request-size controls.
- Expand evaluation datasets and retrieval metrics.
- Add richer LightRAG status polling, database provisioning operations, and fuller TUI forms for domain create/start/stop/remove operations.

