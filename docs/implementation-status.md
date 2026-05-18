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
- Local semantic chunking/indexing with deterministic hashed embeddings for tests and local development.
- Retrieval router with `semantic`, `navigation`, `hybrid`, and `auto` modes; `RetrievalRoutingPolicy` selects local versus remote backend; `LocalRetrievalStrategy` and `LightRAGRetrievalStrategy` in `app/retrieval/strategies.py` dispatch to the router or `LightRAGRemoteRetrievalEngine`.
- Evidence-only retrieval via `POST /query/retrieve`.
- Answer composition via `POST /query/answer` and `POST /query`.
- Admin-only debug details when `include_debug=true`.
- Job table, job status endpoints, Redis `rq` enqueue path, and worker-owned job lifecycle.
- Audit/query log repositories and admin log endpoints.
- Seed admin, backup, and retrieval evaluation scripts.
- Interactive terminal UI: console scripts `context-engine` / `context-tui` (`cli.launcher`) driving `cli/tui/app.py` plus `cli/tui/` navigation, screens, and helpers; `cli/screens/` + `cli/renderers/` supply composable layouts; `cli/flows/` holds multi-step UX; all HTTP via `ApiClient` and `cli/services/`.
- Remote LightRAG integration behind `LIGHTRAG_ENABLED`, including HTTP adapter, domain manifest resolution, retrieval strategy, upload forwarding, and graph proxy routes.
- LightRAG domain deployment control behind `LIGHTRAG_DEPLOY_ENABLED`, including managed domain manifest, generated domain env files, generated compose file, fakeable Docker Compose runner, admin APIs in `app/api/routes/lightrag_admin.py`, user-safe `GET /lightrag/domains`, domain-aware upload/query selection, and matching TUI/admin service wrappers.
- Contract files under `external/lightrag/contract/`.
- Behavior tests for API, terminal client (launcher, settings, TUI, services, API client, screen renderers, query payload), routing policy, LightRAG adapter, LightRAG deploy stack, auth guardrails, upload, retrieval, answer flow, queued jobs, and worker failure handling.

## LightRAG Runtime Behavior

`LIGHTRAG_ENABLED=false` is the default. In that mode, upload/index/retrieval use the local parser, indexes, jobs, and retrieval router.

When `LIGHTRAG_ENABLED=true`:

- `auto`, `semantic`, and `hybrid` retrieval use `LightRAGRemoteRetrievalEngine` and `LightRAGRemoteAdapter`.
- `navigation` retrieval remains local.
- Admin upload stores a local mirror record/file and forwards the file to LightRAG.
- Upload responses may have `job_id: null` because remote ingestion is tracked by LightRAG metadata, not a local indexing job.
- `GET /graphs` and `GET /graph/label/...` proxy to the remote LightRAG service; when LightRAG integration is off, these routes return HTTP `400` (`LightRAG is disabled`).
- LightRAG timeouts/connect failures become `503`; auth/upstream/invalid-response failures become `502`.

## Intentional Simplifications

- Startup table creation is used instead of Alembic migrations.
- Local semantic embeddings use deterministic hashed vectors so tests and local development do not need external embedding credentials.
- Real pgvector column/type usage is not yet the default semantic chunk implementation, even though the Compose database image supports pgvector.
- The answer composer is deterministic and citation-focused. A real LLM provider can be added behind the same composer/provider boundary.
- Document ACLs are deferred; authenticated users can read ready documents.
- LightRAG deployment is not managed by this repo's Compose stack; it is configured as an external service.
- LightRAG domain deployment control is opt-in and generates a separate `.data/lightrag/docker-compose.lightrag-domains.yml`; it does not mutate the root Compose stack.

## Next Hardening Items

- Add Alembic migrations.
- Add production-grade embedding provider and real pgvector column/type usage for semantic chunks.
- Add rate limiting middleware and stronger request-size controls.
- Expand evaluation datasets and retrieval metrics.
- Add richer LightRAG status polling and fuller TUI forms for domain create/start/stop/remove operations.

