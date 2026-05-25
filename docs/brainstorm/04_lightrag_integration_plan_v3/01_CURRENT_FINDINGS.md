# Current Findings: What Exists Now vs What Is Missing

_Last verified against the codebase: May 2026. For a living summary see `docs/implementation-status.md`._

## Implemented now

| Area | Current state | Evidence paths |
|---|---|---|
| Backend API | FastAPI app with auth, admin, documents, jobs, query, LightRAG graph proxy routes | `app/main.py`, `app/api/routes/*` |
| Backend DB | SQLAlchemy tables for users, documents, parsed docs, navigation indexes, semantic chunks, jobs, audit logs, query logs | `app/storage/tables.py` |
| Backend raw upload storage | Uploads saved under `STORAGE_ROOT`, default `.data/uploads` | `app/services/file_storage.py`, `.env.example` |
| Local backend indexing | Parser + navigation + semantic chunks stored in backend DB | `app/services/indexing_service.py`, `app/indexing/semantic_index_builder.py` |
| Local embeddings | Deterministic hash embeddings, 64 dimensions | `app/integrations/lightrag_adapter.py` |
| Background jobs | Redis/RQ queue if `INDEX_JOBS_INLINE=false` | `app/services/job_service.py`, `app/workers/worker.py` |
| Remote LightRAG HTTP client | Retrieve, upload, track status, and graph proxy support | `app/integrations/lightrag_remote_adapter.py` |
| Domain manifest resolver | Maps domain names to base URLs/API keys | `app/integrations/lightrag_domains.py` |
| LightRAG graph API proxy | Authenticated graph endpoints proxied to remote LightRAG | `app/api/routes/lightrag.py` |
| LightRAG domain deployment | Per-domain folders, env, compose manifest; Docker Compose runner | `app/lightrag_deploy/*` |
| Admin domain lifecycle API | Create/list/show/up/down/recreate/regenerate/archive delete | `app/api/routes/lightrag_admin.py`, registered in `app/main.py` |
| User domain listing | Safe subset for query/upload domain pickers | `GET /lightrag/domains` in `lightrag_admin.py` |
| Deploy settings | Runtime + deployment env in config and example file | `app/core/config.py`, `.env.example`, `tests/test_lightrag_deploy_settings.py` |
| Domain-aware upload/query | Optional `lightrag_domain_id` on admin upload and query payloads | `app/api/routes/admin.py`, `app/schemas/query.py`, `app/services/document_service.py` |
| CLI/TUI domain management | Human screens and services for domain lifecycle | `cli/screens/lightrag_domains.py`, `cli/services/lightrag_domains.py`, `cli/tui/screens/main_menu.py` |

## Partially implemented

| Area | Gap |
|---|---|
| Upload engine selection | `DocumentService.upload()` still branches on global `LIGHTRAG_ENABLED`. There is no per-request `local_backend` vs `lightrag` target. `lightrag_domain_id` only applies when remote mode is already enabled. |
| Status lifecycle | Remote upload stores `track_id` and initial status in document metadata. `LightRAGRemoteAdapter.document_status()` exists, but there is no worker, scheduled poller, or admin refresh route that updates local `documents.status` to `READY`. |
| Deploy gating | Mutating domain APIs require `LIGHTRAG_DEPLOY_ENABLED=true`. `GET /lightrag/domains` is available to any authenticated user when the manifest can be read. |
| TUI polish | Domain create/start/stop/remove flows exist but forms and status display are still minimal (see `docs/implementation-status.md`). |

## Missing or unclear

| Area | Why it matters |
|---|---|
| LightRAG service in root Docker Compose | `docker-compose.yml` does not start LightRAG. Domains run via generated `.data/lightrag/docker-compose.lightrag-domains.yml` or an external server. |
| LightRAG storage backend verification | Backend cannot prove exact remote LightRAG internal storage files. It only controls mounted domain folders when using generated compose. |
| Domain access control | No per-user/per-role domain permission model. All authenticated users can list domains and query shared corpora. |
| Same-domain ingestion lock | No Redis/DB lock yet to prevent unsafe simultaneous uploads/indexing into one LightRAG domain. |
| Read/write concurrency inside LightRAG | Must be verified with the LightRAG runtime and storage backend. |
| Status refresh API | No `POST /admin/documents/{document_id}/refresh-lightrag-status` (or equivalent) wired to `document_status()`. |
