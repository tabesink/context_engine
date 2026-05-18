# Coding Agent Prompts

Use one of these after selecting an implementation option.

**Note (May 2026):** Option 1 core work is already in the repository (admin domain API, deploy settings, `GET /lightrag/domains`, CLI/TUI, tests). Use the Option 1 prompt below for **hardening** only. Do not re-implement routes that already exist in `app/api/routes/lightrag_admin.py`.

---

## Prompt for Option 1 — Hardening (recommended next work)

```markdown
You are a senior backend engineer hardening LightRAG integration in `context_engine`.

Repository: https://github.com/tabesink/context_engine.git

Context: Option 1 core deployment is implemented. Do not recreate admin domain routes or deploy settings.

Already implemented — do not duplicate:

- `app/api/routes/lightrag_admin.py` registered in `app/main.py`
- Admin: GET/POST `/admin/lightrag/domains`, GET/POST up/down/recreate/regenerate, DELETE (archive/permanent)
- User: GET `/lightrag/domains` (safe metadata: id, display_name, is_healthy, is_default)
- `app/core/config.py` + `.env.example` deploy settings; `tests/test_lightrag_deploy_*`
- Upload: POST `/admin/documents/upload` with optional `lightrag_domain_id` form field
- Query: `lightrag_domain_id` on `QueryRequest`

Primary goals (remaining gaps):

1. Add explicit upload engine selection: per-request `local_backend` vs `lightrag` (do not rely only on global `LIGHTRAG_ENABLED`).
2. Add status refresh for remote LightRAG uploads using `LightRAGRemoteAdapter.document_status(track_id)` — worker, scheduled job, or admin route such as `POST /admin/documents/{document_id}/refresh-lightrag-status`.
3. Add one-ingestion-at-a-time locking per LightRAG domain (Redis key e.g. `lightrag:domain:<domain_id>:ingest_lock`).
4. Add tests for status refresh and ingest lock; keep existing deploy tests green.

Important files:

- `app/integrations/lightrag_remote_adapter.py` — `document_status()`
- `app/services/document_service.py` — `_upload_remote()`, metadata with `track_id`
- `app/api/routes/admin.py` — upload entrypoint
- `app/services/job_service.py` / `app/workers/worker.py` — if using background poller
- `app/lightrag_deploy/service.py` — domain paths (unchanged unless lock lives here)

Constraints:

- Keep domain data under `.data/lightrag/domains/<domain_id>/`.
- Do not add separate Postgres/Redis services for LightRAG (Option 1).
- Do not remove local backend indexing when `LIGHTRAG_ENABLED=false`.
- Preserve existing admin domain lifecycle APIs and CLI/TUI wrappers.

Acceptance tests:

1. Admin can upload with `engine=local_backend` while `LIGHTRAG_ENABLED=true` (or equivalent explicit field).
2. Admin can upload with `engine=lightrag` and `lightrag_domain_id` without changing global env.
3. Status refresh updates `documents.meta.lightrag.status` and local status to READY when remote reports success.
4. Second concurrent upload to the same domain is rejected or queued with a clear error.
5. Existing domain CRUD and `GET /lightrag/domains` tests still pass.
```

---

## Prompt for Option 1 — Greenfield (historical; core already shipped)

```markdown
You are implementing Option 1 from scratch. Before starting, read `docs/implementation-status.md` — most of this prompt may already be done. Prefer the "Hardening" prompt above unless the branch lacks `lightrag_admin` routes.
```

---

## Prompt for Option 2 — Single Global LightRAG

```markdown
Implement minimal hardening for a single-remote-LightRAG deployment in `context_engine`.

Do not implement dynamic domain deployment (that is Option 1, largely done).

Goals:

1. Make `LIGHTRAG_ENABLED=true` reliably route upload/retrieval/graph calls to `LIGHTRAG_BASE_URL`.
2. Add or extend health check for the configured LightRAG server.
3. Ensure `POST /admin/documents/upload` stores `document_id`, `track_id`, and status in `documents.metadata.lightrag`.
4. Add status refresh endpoint or background poller using `LightRAGRemoteAdapter.document_status()`.
5. Document required `.env` values.

Do not add new Postgres or Redis services.

Acceptance tests:

- Remote LightRAG disabled returns clear error for LightRAG-only actions.
- Remote LightRAG enabled calls configured base URL.
- Upload stores tracking metadata.
- Status refresh updates local document status.
- Query route can use remote LightRAG when enabled.
```

---

## Prompt for Option 3 — Shared Postgres/Redis

```markdown
Evaluate and implement shared PostgreSQL/Redis storage for Context Engine and LightRAG only if LightRAG officially supports those storage backends.

Design constraints:

- One PostgreSQL container.
- One Redis container.
- Separate database/schema/key prefix for Context Engine and each LightRAG domain.
- No shared tables between Context Engine and LightRAG.
- No shared Redis keys without prefixes.

First produce a short design note confirming the exact LightRAG env variables and storage backends. Do not implement until those are confirmed from official LightRAG docs/source.

If confirmed, update:

- `.env.example`
- `app/core/config.py`
- `app/lightrag_deploy/settings.py`
- `app/lightrag_deploy/compose.py`
- deployment docs
- backup/restore docs
- tests

Acceptance tests:

- Generated domain env contains isolated Postgres/Redis settings.
- Two domains do not share DB/schema/key prefix.
- Context Engine RQ keys do not collide with LightRAG keys.
- Backup docs explain all persistent stores.
```

---

## Prompt for Option 5 — Local Backend RAG Only

```markdown
Temporarily defer remote LightRAG. Improve the existing local backend semantic retrieval in `context_engine`.

Goals:

1. Replace JSON/JSONB embedding storage with pgvector.
2. Replace deterministic hash embeddings with a configurable real embedding provider.
3. Keep the existing document upload/indexing job model.
4. Keep one Postgres and one Redis service.
5. Add migration and tests.

Do not remove LightRAG integration code, but keep it disabled by default.

Acceptance tests:

- Existing document upload/index/query works.
- Embeddings are stored in pgvector column.
- Retrieval uses vector similarity in Postgres.
- App still works with 5–10 concurrent users.
```
