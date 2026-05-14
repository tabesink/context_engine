# Implementation Status

This file records what the current codebase implements against `docs/implementation-plan.md`.

## Complete In Current Slice

- Documentation plan, architecture guide, junior guide, reference reuse plan, and initial ADRs.
- FastAPI app factory and health endpoints.
- SQLAlchemy storage models and table creation on startup.
- JWT auth, password hashing, `/auth/login`, `/auth/me`, `get_current_user`, and `require_admin`.
- Admin upload/index/reindex/delete/list endpoints.
- Authenticated document list/detail/structure/page endpoints.
- Text, Markdown, and PDF parsing.
- Navigation index builder and PageIndex-style adapter.
- Deterministic LightRAG-style semantic adapter and chunk indexing.
- Retrieval router with semantic/navigation/hybrid/auto modes.
- Evidence-only and answer endpoints.
- Job table, job status endpoints, Redis `rq` enqueue path, and worker-owned job status lifecycle.
- Audit/query log repositories and admin log endpoints.
- Seed admin, backup, and evaluation placeholder scripts.
- API behavior tests for health, auth guardrails, upload, retrieval, answer flow, queued jobs, and worker failure handling.

## Intentional V1 Simplifications

- Indexing can still run inline when `INDEX_JOBS_INLINE=true`, which keeps tests and local development deterministic. Production defaults to Redis `rq` enqueueing.
- Semantic embeddings use deterministic hashed vectors so tests and local development do not need external embedding credentials.
- The answer composer is deterministic and citation-focused. A real LLM provider can be added behind the same composer/provider boundary.
- Document ACLs are deferred; authenticated users can read ready documents.

## Next Hardening Items

- Add Alembic migrations instead of startup table creation.
- Add real pgvector column/type usage for semantic chunks.
- Add rate limiting middleware.
- Expand evaluation dataset and retrieval metrics.

