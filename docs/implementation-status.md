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
- Retrieval router with `semantic`, `navigation`, `hybrid`, and `auto` modes, plus a routing policy Module that decides local versus remote execution.
- Evidence-only retrieval via `POST /query/retrieve`.
- Answer composition via `POST /query/answer` and `POST /query`.
- Admin-only debug details when `include_debug=true`.
- Job table, job status endpoints, Redis `rq` enqueue path, and worker-owned job lifecycle.
- Audit/query log repositories and admin log endpoints.
- Seed admin, backup, and retrieval evaluation scripts.
- Typer `ragcli` with auth/session, documents, query, admin documents, logs, jobs, LightRAG graph commands, and explicit unsupported planned command groups.
- Remote LightRAG integration behind `LIGHTRAG_ENABLED`, including HTTP adapter, domain manifest resolution, retrieval strategy, upload forwarding, and graph proxy routes.
- Contract files under `external/lightrag/contract/`.
- Behavior tests for API, CLI, LightRAG adapter, auth guardrails, upload, retrieval, answer flow, queued jobs, and worker failure handling.

## LightRAG Runtime Behavior

`LIGHTRAG_ENABLED=false` is the default. In that mode, upload/index/retrieval use the local parser, indexes, jobs, and retrieval router.

When `LIGHTRAG_ENABLED=true`:

- `auto`, `semantic`, and `hybrid` retrieval use `LightRAGRemoteRetrievalEngine` and `LightRAGRemoteAdapter`.
- `navigation` retrieval remains local.
- Admin upload stores a local mirror record/file and forwards the file to LightRAG.
- Upload responses may have `job_id: null` because remote ingestion is tracked by LightRAG metadata, not a local indexing job.
- `GET /graphs` and `GET /graph/label/...` proxy to the remote LightRAG service.
- LightRAG timeouts/connect failures become `503`; auth/upstream/invalid-response failures become `502`.

## Intentional Simplifications

- Startup table creation is used instead of Alembic migrations.
- Local semantic embeddings use deterministic hashed vectors so tests and local development do not need external embedding credentials.
- Real pgvector column/type usage is not yet the default semantic chunk implementation, even though the Compose database image supports pgvector.
- The answer composer is deterministic and citation-focused. A real LLM provider can be added behind the same composer/provider boundary.
- Document ACLs are deferred; authenticated users can read ready documents.
- LightRAG deployment is not managed by this repo's Compose stack; it is configured as an external service.

## Next Hardening Items

- Add Alembic migrations.
- Add production-grade embedding provider and real pgvector column/type usage for semantic chunks.
- Add rate limiting middleware and stronger request-size controls.
- Expand evaluation datasets and retrieval metrics.
- Add richer LightRAG status polling or domain administration only after stable backend admin routes are designed.

