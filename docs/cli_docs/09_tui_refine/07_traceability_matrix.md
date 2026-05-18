# 7. Traceability Matrix

| TUI Screen | User Intent | Backend Route | Default View | Inspect View | Admin? | Backend Gap? |
|---|---|---|---|---|---:|---:|
| Login | Authenticate | `POST /auth/login` | Email/password form | Request shape, status, saved-session summary | No | No |
| Session | Current identity | `GET /auth/me` | User email/role | Raw user JSON | No | No |
| Documents | Browse ready docs | `GET /documents` | Document table | Full IDs, response count, raw JSON | No | No |
| Document Detail | View one doc | `GET /documents/{id}` | Metadata summary | Full metadata JSON | No | No |
| Document Structure | View outline | `GET /documents/{id}/structure` | Tree/table | Full structure JSON | No | No |
| Document Page | View page text | `GET /documents/{id}/pages/{page}` | Page text excerpt | Full page payload | No | No |
| Documents Admin Actions | Upload/list/index/delete | `/admin/documents...` | Admin action menu | Route/payload/status | Yes | No |
| Retrieval | Retrieve evidence | `POST /query/retrieve` | Query form/result table | Request JSON, evidence IDs, raw response | No | No |
| Answer | Generate answer | `POST /query/answer` or `POST /query` | Answer + sources | Request JSON, evidence, raw answer payload | No | No |
| Retrieval Compare | Compare modes | repeated `POST /query/retrieve` | Mode comparison table | Per-mode payload/status/errors | No | No |
| Graphs | Graph labels/summary | `/graphs`, `/graph/label/...` | Labels/summary table | Params, node/edge counts, raw JSON | No | No |
| LightRAG Domains | Deploy/manage domains | `/admin/lightrag/domains...` | Domain table/actions | Manifest path, compose path, Docker status | Yes | No |
| Domain Selector | Choose query domain | `GET /lightrag/domains` | Domain dropdown/list | User-safe domain payload | No | No |
| Jobs | Monitor indexing | `GET /jobs` | Jobs table | Full job metadata/raw JSON | Yes | No |
| Job Detail | Inspect one job | `GET /jobs/{job_id}` | Job status/error | Full metadata, retry info | Yes | No |
| Job Retry | Retry failed job | `POST /jobs/{job_id}/retry` | Retry result | Request/status/new job ID | Yes | No |
| Observability | Audit/query logs | `/admin/query-logs`, `/admin/audit-logs` | Recent logs | Full log metadata | Yes | No |
| Health / Readiness | System debug | `/health`, `/health/readiness`, future status routes | Check table | Raw response and latency | Partial | Partial |
| Backend Gaps | Unsupported capabilities | none | Gap table | Suggested route and implementation note | Dev | Yes |

## Traceability Rules

1. Every TUI screen must list its backend route or say `local only` / `backend gap`.
2. Every API-backed screen must expose inspect mode.
3. Every table should have a raw JSON fallback.
4. Every admin screen must rely on backend auth, not local permission guesses.
5. Backend gaps must never fake success.
