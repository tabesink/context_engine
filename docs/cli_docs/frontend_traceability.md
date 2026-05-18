# Frontend Traceability Matrix

Maps **`context-engine` / `context-tui` TUI screens and flows** to future browser surfaces. There is no parallel Typer command tree.

| Frontend Screen | Terminal client | Backend Routes | Status | Gaps |
|---|---|---|---|---|
| Session | Login + Session summary | `GET /auth/me` | Implemented | TUI shows saved session summary only; no token output |
| Document Library | Documents | `GET /documents` | Implemented | None |
| Document Detail | Documents drill-in | `GET /documents/{id}` | Implemented | Depth depends on TUI iteration |
| Document Structure | Documents → structure | `GET /documents/{id}/structure` | Implemented | Textual tree |
| Document Page | Documents → page | `GET /documents/{id}/pages/{page}` | Implemented | Textual body |
| Retrieval | Retrieval | `POST /query/retrieve` | Implemented | Default retrieval params follow screen |
| Answer | Retrieval / answer paths | `POST /query`, `POST /query/answer` | Implemented | None |
| Retrieval Compare | Retrieval compare flow (if enabled) | `POST /query/retrieve` per mode | Implemented | Partial failures render per mode |
| Retrieval Domain Selector | Retrieval domain field | `GET /lightrag/domains`, `POST /query/retrieve` with `lightrag_domain_id` | Implemented | Defaults to backend/user domain list |
| LightRAG Labels | Graphs | `GET /graph/label/list`, `GET /graph/label/popular`, `GET /graph/label/search` | Implemented | Often starts with popular labels |
| Graph Summary | Graphs | `GET /graphs` | Implemented | Summaries only in-terminal; use JSON from API for viz |
| LightRAG Domain Admin | LightRAG Domains and lifecycle forms | `GET /admin/lightrag/domains`, `POST /admin/lightrag/domains`, `/up`, `/down`, `/recreate`, `DELETE /admin/lightrag/domains/{id}` | Implemented | Permanent delete requires backend flag and typed confirmation |
| Documents Admin Actions | Documents -> Admin Actions | `GET /admin/documents` | Implemented | Authorization from backend responses |
| Admin Upload Flow | Documents -> Admin Actions -> Upload | `POST /admin/documents/upload`, optional `GET /jobs/{job_id}` | Implemented | None |
| Jobs | Jobs | `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/retry` | Implemented | None |
| Observability | Observability | `GET /admin/audit-logs`, `GET /admin/query-logs` | Implemented | Read-only |
| Admin Dashboard | Composite admin views | `GET /admin/documents`, `GET /jobs`, `GET /admin/query-logs` | Implemented | Corpus lifecycle routes still backend gaps |
| Backend Gaps Doc | Documentation only | None until routes exist | Documented | See `docs/cli_docs/backend_gaps.md`; not a TUI root screen |

## Rules Preserved

- Raw JSON from the API remains the stable automation contract.
- Human and TUI output share screen builders where practical.
- The client does not call LightRAG directly.
- Admin permissions are not inferred locally; backend `403` responses render as backend errors.
- Tokens, bearer strings, passwords, API keys, and multipart file bytes are not printed.
- API-backed screens keep clean defaults and expose inspect/raw JSON views on demand.
