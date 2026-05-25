# 2. API Surface Inventory

This inventory is based on the mounted routers in `app.main` and route files in `app/api/routes/`.

## 2.1 Route Groups

| Router File | Prefix | Main Purpose |
|---|---:|---|
| `app/api/routes/health.py` | none | Health/readiness probes. |
| `app/api/routes/auth.py` | `/auth` | Login and current-user identity. |
| `app/api/routes/documents.py` | `/documents` | Normal user document read APIs. |
| `app/api/routes/admin.py` | `/admin` | Admin-only upload/index/delete/log APIs. |
| `app/api/routes/query.py` | `/query` | Retrieval and answer APIs. |
| `app/api/routes/lightrag.py` | none | LightRAG graph proxy APIs. |
| `app/api/routes/jobs.py` | `/jobs` | Admin-only job inspection/retry. |

## 2.2 Common Auth Dependencies

| Dependency | File | Behavior |
|---|---|---|
| `get_current_user` | `app/api/deps.py` | Reads bearer token, decodes JWT, loads active user by id. |
| `require_admin` | `app/api/deps.py` | Requires current user role to equal admin. Raises 403 otherwise. |
| `get_session` | `app/storage/db.py` | Yields SQLAlchemy session and closes it after request. |

## 2.3 Health APIs

| Method | Path | Auth | Purpose | Key Code Path |
|---|---|---|---|---|
| GET | `/health` | Public | Basic liveness; returns `{"status":"ok"}`. | `app/api/routes/health.py` |
| GET | `/health/readiness` | Public | Basic readiness; returns `{"status":"ready"}`. | `app/api/routes/health.py` |

## 2.4 Auth APIs

| Method | Path | Auth | Request | Response | Purpose | Key Code Path |
|---|---|---|---|---|---|---|
| POST | `/auth/login` | Public | `LoginRequest` | `TokenResponse` | Validates email/password and returns JWT bearer token. | `app/api/routes/auth.py`, `UserRepository`, `verify_password`, `create_access_token` |
| GET | `/auth/me` | User token | none | `UserRead` | Returns current authenticated user. | `app/api/routes/auth.py`, `get_current_user` |

## 2.5 Normal User Document APIs

These require `get_current_user`. They only expose documents that are ready through `DocumentService.get_ready_or_404` or `DocumentRepository.list_ready`.

| Method | Path | Auth | Purpose | Key Code Path |
|---|---|---|---|---|
| GET | `/documents` | User | List ready documents. | `app/api/routes/documents.py`, `DocumentRepository.list_ready` |
| GET | `/documents/{document_id}` | User | Read ready document details. | `DocumentService.get_ready_or_404` |
| GET | `/documents/{document_id}/structure` | User | Return navigation tree for ready document. | `DocumentRepository.get_navigation_tree` |
| GET | `/documents/{document_id}/pages/{page_number}` | User | Return parsed page content/metadata for ready document. | `DocumentRepository.get_parsed`, parsed pages lookup |

## 2.6 Admin APIs

These require `require_admin`.

| Method | Path | Auth | Purpose | Key Code Path |
|---|---|---|---|---|
| GET | `/admin/ping` | Admin | Simple admin guardrail check. | `app/api/routes/admin.py` |
| POST | `/admin/documents/upload` | Admin | Upload file, create document, start/queue indexing or upload to LightRAG. | `DocumentService.upload` |
| POST | `/admin/documents/{document_id}/index` | Admin | Enqueue index job for a document. | `JobService.enqueue_index_document` |
| POST | `/admin/documents/{document_id}/reindex` | Admin | Enqueue reindex job for a document. | `JobService.enqueue_index_document` |
| DELETE | `/admin/documents/{document_id}` | Admin | Mark document deleted and audit. | `DocumentService.delete` |
| GET | `/admin/documents` | Admin | List all documents, not only ready documents. | `DocumentRepository.list_all` |
| GET | `/admin/audit-logs` | Admin | Return recent audit logs. | `LogRepository.list_audit` |
| GET | `/admin/query-logs` | Admin | Return recent query logs. | `LogRepository.list_query_logs` |

## 2.7 Query APIs

These require `get_current_user`.

| Method | Path | Auth | Request | Response | Purpose | Key Code Path |
|---|---|---|---|---|---|---|
| POST | `/query/retrieve` | User | `QueryRequest` | `RetrieveResponse` | Return evidence/context only. | `RetrievalService.retrieve` |
| POST | `/query/answer` | User | `QueryRequest` | `QueryResponse` | Retrieve evidence and compose answer. | `RetrievalService.answer`, `AnswerComposer` |
| POST | `/query` | User | `QueryRequest` | `QueryResponse` | Convenience alias for answer. | `RetrievalService.answer` |

Notes:

- Retrieval mode options appear to include `auto`, `semantic`, `navigation`, and `hybrid` based on CLI and schemas.
- Debug information is only included when `include_debug=true` and the user role is admin.
- Queries are logged through `LogRepository.record_query`.

## 2.8 LightRAG Graph Proxy APIs

These require `get_current_user` and proxy to a remote LightRAG service through `LightRAGRemoteAdapter`. They are mounted directly at root-level paths, not under `/lightrag`.

| Method | Path | Auth | Purpose | Key Code Path |
|---|---|---|---|---|
| GET | `/graphs` | User | Proxy graph retrieval, usually with label/depth/max_nodes params. | `app/api/routes/lightrag.py`, `LightRAGRemoteAdapter.get_json` |
| GET | `/graph/label/list` | User | Proxy label list. | `LightRAGRemoteAdapter.get_json` |
| GET | `/graph/label/popular` | User | Proxy popular labels. | `LightRAGRemoteAdapter.get_json` |
| GET | `/graph/label/search` | User | Proxy label search. | `LightRAGRemoteAdapter.get_json` |

Important design note: these endpoints expose graph visualization capabilities while keeping the actual LightRAG service behind a single adapter layer.

## 2.9 Job APIs

These require `require_admin`.

| Method | Path | Auth | Purpose | Key Code Path |
|---|---|---|---|---|
| GET | `/jobs` | Admin | List jobs. | `JobRepository.list_all` |
| GET | `/jobs/{job_id}` | Admin | Read one job. | `JobRepository.get` |
| POST | `/jobs/{job_id}/retry` | Admin | Retry/run a job. | `JobService.run_index_job` |

## 2.10 API Design Observations

Strong points:

- API route files are grouped by user-facing capability.
- Most route handlers are thin and call service/repository layers.
- Admin and user API surfaces are clearly separated.
- CLI commands mostly mirror existing backend endpoints.

Potential improvements:

- Consider adding explicit OpenAPI tags/descriptions for future frontend developers.
- Consider grouping LightRAG graph routes under a prefix like `/lightrag` or `/graph` if frontend naming clarity matters. Current paths mirror upstream LightRAG routes, which is useful but less namespaced.
- Consider adding pagination/limits to document/job/log list endpoints if data volume grows.
