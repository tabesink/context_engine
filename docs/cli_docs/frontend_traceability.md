# Frontend Traceability Matrix

This matrix maps the API-first `ragcli` screens and flows to future frontend surfaces.

| Frontend Screen | CLI/TUI Equivalent | Backend Routes | Status | Gaps |
|---|---|---|---|---|
| Session | `ragcli auth me`, TUI Session | `GET /auth/me` | Implemented | TUI shows saved session summary only; no token output |
| Document Library | `ragcli documents list`, `ragcli screen documents`, TUI Documents | `GET /documents` | Implemented | None |
| Document Detail | `ragcli documents show` | `GET /documents/{id}` | Implemented | No TUI detail drill-in yet |
| Document Structure | `ragcli documents structure` | `GET /documents/{id}/structure` | Implemented | Human view is textual |
| Document Page | `ragcli documents page` | `GET /documents/{id}/pages/{page}` | Implemented | Human view is textual |
| Retrieval | `ragcli documents retrieve`, `ragcli screen retrieval`, TUI Retrieval | `POST /query/retrieve` | Implemented | TUI uses default retrieval settings |
| Answer | `ragcli query`, `ragcli documents answer` | `POST /query`, `POST /query/answer` | Implemented | None |
| Retrieval Compare | `ragcli retrieval compare` | `POST /query/retrieve` for each mode | Implemented | Partial failures render per mode |
| LightRAG Labels | `ragcli lightrag labels list/popular/search`, TUI LightRAG Graphs | `GET /graph/label/list`, `GET /graph/label/popular`, `GET /graph/label/search` | Implemented | TUI starts with popular labels |
| Graph Summary | `ragcli lightrag graphs show`, `ragcli screen graph` | `GET /graphs` | Implemented | Terminal view summarizes only; use JSON for visualization |
| Admin Documents | `ragcli admin documents list`, TUI Admin Documents | `GET /admin/documents` | Implemented | Authorization comes from backend responses |
| Admin Upload Flow | `ragcli admin documents upload-flow` | `POST /admin/documents/upload`, optional `GET /jobs/{job_id}` | Implemented | None |
| Jobs | `ragcli jobs list/status/retry`, TUI Jobs | `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/retry` | Implemented | None |
| Observability | `ragcli admin audit-logs list`, `ragcli admin query-logs list`, TUI Observability | `GET /admin/audit-logs`, `GET /admin/query-logs` | Implemented | TUI is read-only |
| Admin Dashboard | `ragcli admin dashboard`, `ragcli screen admin` | `GET /admin/documents`, `GET /jobs`, `GET /admin/query-logs` | Implemented | Corpus lifecycle routes still backend gaps |
| Backend Gaps | `ragcli screen gaps`, TUI Backend Gaps, planned commands | None until backend routes exist | Implemented as gaps | Chat, users, conversations, messages, runs, approvals, corpus publish/rollback/cleanup |

## Rules Preserved

- Existing supported JSON output remains raw and script-safe.
- Human and TUI output use shared screen builders where practical.
- The CLI does not call LightRAG directly.
- Admin permissions are not inferred locally; backend `403` responses are rendered as backend errors.
- Tokens, bearer strings, and passwords are not printed.
