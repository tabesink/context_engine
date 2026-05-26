# 1. UX Diagnosis

## 1.1 What Is Already Good

The existing ASCII screen plan has the right underlying goal: the terminal UI mirrors backend API surfaces and lets developers/operators see what routes are called, which capabilities are admin-only, and which features are backend gaps.

Strong points:

- Each screen maps to a backend capability.
- Screens show the backend route being called.
- Admin-only surfaces are identified.
- Planned backend gaps are documented instead of pretending they work.
- Retrieval, document, job, graph, and observability surfaces are represented.
- ASCII-style layouts are portable across terminals and good for junior developers.
- The TUI can act as a future browser-frontend traceability prototype.

## 1.2 What Feels Too Cluttered

Some screens show too much route/request/response detail in the main body.

Examples of clutter risks:

- Showing route, request payload, response fields, related commands, and controls all on every default screen.
- Showing long document IDs in default tables.
- Having both `Documents` and `Admin Documents` as root items.
- Having both `LightRAG Domains` and separate root-level LightRAG CRUD actions.
- Showing implementation labels such as `LightRAG Graphs` at the root.
- Putting every possible action directly in a root menu instead of nesting actions inside capability areas.

## 1.3 What Is Missing for API Debugging

The TUI should expose more backend/API detail, but not by default.

Missing or underdeveloped debug affordances:

- A reusable API inspect drawer.
- Raw JSON view for actual backend response.
- Full ID toggle.
- Request payload preview before submit.
- HTTP status and latency in a consistent footer.
- Admin-only debug payload visibility.
- Clear route mapping for multipart upload and DELETE operations.
- A consistent error detail panel with backend route, status code, message, and next action.
- A consistent backend gap panel that states missing route and suggested next implementation step.

## 1.4 Main UX Recommendation

Use progressive disclosure.

```text
Default screen:
  - clean title
  - route/status hint in footer
  - compact table or summary
  - primary actions only

Inspect screen:
  - method and route
  - query params or request payload
  - status code and latency
  - response summary
  - selected IDs
  - raw JSON option
```

This preserves the TUI as a backend/API testing tool without turning every screen into a wall of text.

## 1.5 Label Improvements

| Current Label | Recommended Label | Reason |
|---|---|---|
| `LightRAG Graphs` | `Graphs` | User-facing capability, not implementation detail. |
| `Admin Documents` | `Documents > Admin Actions` | Avoid duplicate top-level document concept. |
| `Create LightRAG Domain` at root | `LightRAG Domains > Create Domain` | CRUD belongs inside the domain screen. |
| `Start LightRAG Domain` at root | `LightRAG Domains > Start Domain` | Same. |
| `Stop LightRAG Domain` at root | `LightRAG Domains > Stop Domain` | Same. |
| `Recreate LightRAG Domain` at root | `LightRAG Domains > Recreate Domain` | Same. |
| `Remove LightRAG Domain` at root | `LightRAG Domains > Archive Remove Domain` | More explicit and safer. |

## 1.6 Final Design Principle

```text
Do not remove information.
Move information to the correct layer.
```

That means:

- root menu = capability areas
- default screen = useful summary
- inspect drawer = route/payload/response details
- raw JSON = full backend shape
- backend gap screen = honest unsupported features


---

# 2. Root Menu and Navigation

## 2.1 Admin Root Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8000
Session: admin@example.com
Role:    admin

> Documents
  Retrieval
  Graphs
  LightRAG Domains
  Jobs
  Observability
  Health / Readiness
  Backend Gaps
  Logout
  Quit
```

## 2.2 Normal User Root Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8000
Session: user@example.com
Role:    user

> Documents
  Retrieval
  Graphs
  Health / Readiness
  Logout
  Quit
```

## 2.3 Role Visibility

| Item | Normal User | Admin | Notes |
|---|---:|---:|---|
| Documents | Yes | Yes | Admin sees nested admin actions. |
| Retrieval | Yes | Yes | Domain selection available if backend supports it. |
| Graphs | Yes | Yes | Backend controls LightRAG availability. |
| LightRAG Domains | No | Yes | Admin deployment/control surface. |
| Jobs | No | Yes | Admin-only indexing job monitor. |
| Observability | No | Yes | Audit/query logs are admin-only. |
| Health / Readiness | Yes | Yes | User-safe subset can be shown to normal users. |
| Backend Gaps | Dev only | Dev only | Hide in production unless useful for debugging. |
| Logout | Yes | Yes | Local session clear. |
| Quit | Yes | Yes | Exit TUI. |

## 2.4 Navigation Hierarchy

```text
Root
  ├── Documents
  │     ├── Browse Ready Documents
  │     ├── Document Detail
  │     ├── Structure / Outline
  │     ├── Page Preview
  │     └── Admin Actions
  │           ├── Upload Document
  │           ├── List All Documents
  │           ├── Rebuild Structure
  │           ├── Reingest LightRAG
  │           ├── Refresh LightRAG Status
  │           └── Delete Document
  │
  ├── Retrieval
  │     ├── Retrieval Preview
  │     ├── Citation Answer
  │     ├── Compare Modes
  │     └── Domain Selector
  │
  ├── Graphs
  │     ├── Popular Labels
  │     ├── Search Labels
  │     ├── Label Catalog
  │     └── Graph Summary
  │
  ├── LightRAG Domains
  │     ├── List Domains
  │     ├── Create Domain
  │     ├── Show Domain Detail
  │     ├── Start Domain
  │     ├── Stop Domain
  │     ├── Recreate Domain
  │     ├── Regenerate Domain Files
  │     ├── Archive Remove Domain
  │     └── Permanent Delete Domain
  │
  ├── Jobs
  │     ├── List Jobs
  │     ├── Job Detail
  │     └── Retry Failed Job
  │
  ├── Observability
  │     ├── Query Logs
  │     └── Audit Logs
  │
  ├── Health / Readiness
  │     ├── API Health
  │     ├── Readiness
  │     ├── Storage Status
  │     ├── Worker / Redis Status
  │     ├── LightRAG Runtime Status
  │     └── LightRAG Deploy Status
  │
  └── Backend Gaps
```

## 2.5 Root Menu Rules

- Root menu should contain no direct CRUD actions.
- Root menu should contain no duplicate domain concepts.
- Root menu should use user-facing labels, not implementation labels.
- Root menu should hide admin-only areas when user role is known.
- Backend still enforces authorization. UI hiding is convenience only.
- Development-only screens should be clearly labeled and optionally hidden outside local/dev mode.


---

# 3. Global Screen Template

## 3.1 Standard Screen Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ CONTEXT ENGINE / Documents                                   │
│ Backend: http://127.0.0.1:8000   User: admin@example.com      │
├──────────────────────────────────────────────────────────────┤
│ Summary / Data                                               │
│                                                              │
│ +------------+-------------+---------+---------+-------------+
│ | id         | filename    | status  | pages   | updated     |
│ +------------+-------------+---------+---------+-------------+
│ | doc_01f... | manual.pdf  | ready   | 124     | 2026-05-18  |
│ +------------+-------------+---------+---------+-------------+
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Actions                                                      │
│ > Open selected                                              │
│   Refresh                                                    │
│   Inspect API                                                │
│   Back                                                       │
├──────────────────────────────────────────────────────────────┤
│ Route: GET /documents        Status: 200       Time: 42 ms   │
│ Keys: ↑/↓ Move  Enter Select  I Inspect  R Refresh  B Back   │
└──────────────────────────────────────────────────────────────┘
```

## 3.2 Screen Regions

| Region | Purpose | Rule |
|---|---|---|
| Header | Screen title and breadcrumb. | Keep one or two lines. |
| Session strip | Backend URL and user/session. | Do not show token. |
| Main body | Table, result, form, or message. | Maximize signal, reduce boilerplate. |
| Actions | Available next actions. | 3–8 actions max. |
| Route footer | Method/path/status/latency. | Compact one-line hint. |
| Key footer | Common controls. | Consistent across screens. |

## 3.3 Route Footer

Every API-backed screen should show a compact route footer:

```text
Route: POST /retrieve    Status: 200    Time: 63 ms
```

For local-only screens:

```text
Local: credential store clear    Status: done
```

For backend gaps:

```text
Route: none    Status: backend gap
```

## 3.4 Keyboard Model

| Key | Meaning |
|---|---|
| `↑/↓` | Move selection. |
| `Enter` | Select / submit. |
| `R` | Refresh current API-backed screen. |
| `I` | Inspect API request/response. |
| `J` | Raw JSON response. |
| `F` | Toggle full IDs. |
| `D` | Debug details, admin-only. |
| `B` | Back. |
| `Q` | Quit. |

## 3.5 Table Rules

Default tables should show only useful columns.

Rules:

- 5–7 columns max.
- ID columns truncated by default.
- Dates shortened by default.
- Avoid wide JSON blobs in tables.
- Avoid showing metadata dicts in tables.
- Use `F` to reveal full IDs.
- Use `I` or `J` for full payloads.

## 3.6 Empty State Template

```text
┌──────────────────────────────────────────────────────────────┐
│ CONTEXT ENGINE / Documents                                   │
├──────────────────────────────────────────────────────────────┤
│ No documents found.                                          │
│                                                              │
│ Next:                                                        │
│ > Refresh                                                    │
│   Upload Document       admin only                           │
│   Back                                                       │
├──────────────────────────────────────────────────────────────┤
│ Route: GET /documents        Status: 200       Time: 28 ms   │
│ Keys: Enter Select  R Refresh  I Inspect  B Back             │
└──────────────────────────────────────────────────────────────┘
```

## 3.7 Loading State Template

```text
CONTEXT ENGINE / Retrieval

Loading...
Route: POST /retrieve
```

Keep loading states simple.

## 3.8 Error State Template

```text
ERROR

code:    forbidden
message: Admin access required
route:   POST /admin/documents/upload
status:  403

Next:
> Back
  Check current session
```

No stack traces by default.


---

# 4. Progressive Disclosure Model

## 4.1 Why Progressive Disclosure

The TUI has two jobs:

1. normal operation, and
2. backend/API debugging.

If every route, payload, raw response, ID, and debug object is always visible, the screen becomes unusable. Instead, expose detail on demand.

## 4.2 Modes

| Mode | Key | Purpose |
|---|---:|---|
| Normal | default | Clean operator summary. |
| Inspect API | `I` | Method, route, params, payload, status, latency, response summary. |
| Raw JSON | `J` | Pretty-printed backend response. |
| Full IDs | `F` | Expand truncated IDs in tables/details. |
| Debug | `D` | Admin-only backend debug payload if returned. |
| Error Detail | automatic or `I` | Structured backend error and next action. |

## 4.3 API Inspect Drawer

Example:

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: POST                                                 │
│ Route:  /query/retrieve                                      │
│ Status: 200 OK                                               │
│ Time:   63 ms                                                │
│                                                              │
│ Request JSON                                                 │
│ {                                                            │
│   "query": "reset procedure",                                │
│   "mode": "hybrid",                                          │
│   "top_k": 8,                                                │
│   "lightrag_domain_id": "fatigue"                            │
│ }                                                            │
│                                                              │
│ Response Summary                                             │
│ evidence_count: 8                                            │
│ engines: semantic, navigation                                │
│ debug: omitted                                               │
└──────────────────────────────────────────────────────────────┘
```

## 4.4 GET Inspect Variant

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: GET                                                  │
│ Route:  /documents                                           │
│ Status: 200 OK                                               │
│ Time:   37 ms                                                │
│ Query Params: none                                           │
│                                                              │
│ Response Summary                                             │
│ documents_count: 12                                          │
│ ready_count: 12                                              │
└──────────────────────────────────────────────────────────────┘
```

## 4.5 Multipart Upload Inspect Variant

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: POST                                                 │
│ Route:  /admin/documents/upload                              │
│ Status: 202 Accepted                                         │
│ Time:   181 ms                                               │
│                                                              │
│ Multipart Request                                            │
│ file.name: manual.pdf                                        │
│ file.size: 2.4 MB                                            │
│ lightrag_domain_id: fatigue                                  │
│                                                              │
│ Response Summary                                             │
│ document_id: doc_01f8a9...                                   │
│ status: indexing                                             │
│ job_id: job_77b32c...                                        │
└──────────────────────────────────────────────────────────────┘
```

## 4.6 DELETE Inspect Variant

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: DELETE                                               │
│ Route:  /admin/lightrag/domains/fatigue                      │
│ Status: 200 OK                                               │
│ Time:   94 ms                                                │
│                                                              │
│ Request                                                      │
│ permanent: false                                             │
│ confirmation: ARCHIVE fatigue                                │
│                                                              │
│ Response Summary                                             │
│ archived: true                                               │
│ archive_path: .data/lightrag/deleted/fatigue-2026...         │
└──────────────────────────────────────────────────────────────┘
```

## 4.7 Raw JSON View

```text
┌─ RAW JSON ───────────────────────────────────────────────────┐
│ {                                                            │
│   "documents": [                                             │
│     {                                                        │
│       "id": "doc_01f8a9...",                                 │
│       "filename": "manual.pdf",                              │
│       "status": "ready"                                      │
│     }                                                        │
│   ]                                                          │
│ }                                                            │
├──────────────────────────────────────────────────────────────┤
│ Keys: J Close  F Full IDs  B Back                            │
└──────────────────────────────────────────────────────────────┘
```

Raw JSON rules:

- Pretty-print with indentation.
- Redact tokens, passwords, API keys.
- Truncate very large fields by default.
- Show filename/size for file uploads, never file bytes.
- Allow “show more” for long text fields if current TUI supports it.

## 4.8 Full ID Toggle

Default:

```text
doc_01f8a9...
job_77b32c...
```

Full ID mode:

```text
doc_01f8a9b9-8f3c-4b0a-8f9a-4c21e6a65c25
job_77b32c81-1c44-48d0-9c3c-f097df331983
```

Use `F` consistently.

## 4.9 Debug Mode

Debug mode is admin-only and only shows what the backend returned.

If backend omits debug payload:

```text
Debug: not returned by backend
```

If user is not admin:

```text
Debug: admin-only
```

Do not synthesize backend debug fields in the TUI.


---

# 5. Screen-Specific Refinements

## 5.1 Documents

### Default table

```text
+------------+----------------------+----------+-------+------------+
| id         | filename             | status   | pages | updated    |
+------------+----------------------+----------+-------+------------+
| doc_01f... | manual.pdf           | ready    | 124   | 2026-05-18 |
| doc_05b... | catalog.pdf          | ready    | 42    | 2026-05-18 |
+------------+----------------------+----------+-------+------------+
```

### Default actions

```text
> Open selected
  View structure
  View page
  Retrieve from selected
  Admin Actions        admin only
  Refresh
  Inspect API
  Back
```

### Backend routes

```text
GET /documents
GET /documents/{document_id}
GET /documents/{document_id}/structure
GET /documents/{document_id}/pages/{page_number}
```

### Inspect fields

- method and route
- status code
- latency
- document count
- selected document full ID
- raw JSON response

## 5.2 Documents > Admin Actions

### Actions

```text
> Upload document
  List all documents
  Reingest selected
  Refresh status selected
  Delete selected
  Back
```

### Backend routes

```text
GET    /admin/documents
POST   /admin/documents/upload
POST   /admin/documents/{document_id}/reingest
POST   /admin/documents/{document_id}/refresh-status
DELETE /admin/documents/{document_id}
```

### Delete confirmation

```text
DELETE DOCUMENT

Document: manual.pdf
ID:       doc_01f8a9...

This should soft-delete the document through the backend.

Type DELETE doc_01f8a9 to continue:
```

## 5.3 Retrieval

### Prompt screen fields

```text
Query:              [reset procedure________________]
Mode:               auto
LightRAG domain:    fatigue
Top K:              8
Document filter:    none
General fallback:   false
Debug requested:    false
```

### Result table

```text
+---+------------+----------+-------+-------+----------------+
| # | engine     | score    | pages | doc   | section        |
+---+------------+----------+-------+-------+----------------+
| 1 | semantic   | 0.91     | 19-21 | doc_1 | Pendant Reset  |
| 2 | navigation | 0.84     | 7     | doc_5 | Setup          |
+---+------------+----------+-------+-------+----------------+
```

### Backend routes

```text
POST /retrieve
```

### Inspect fields

- full request payload
- selected `lightrag_domain_id`
- selected `document_ids`
- evidence count
- evidence IDs
- engines returned
- raw JSON

## 5.4 Graphs

Rename screen from:

```text
LightRAG Graphs
```

to:

```text
Graphs
```

### Actions

```text
> Popular labels
  Search labels
  Label catalog
  Graph summary
  Back
```

### Routes

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

### Inspect fields

- label
- max depth
- max nodes
- node count
- edge count
- route
- raw graph JSON option

## 5.5 LightRAG Domains

### Default table

```text
+----------+------+----------+----------+---------+------------+
| domain   | port | runtime  | health   | default | updated    |
+----------+------+----------+----------+---------+------------+
| fatigue  | 9622 | running  | healthy  | yes     | 2026-05-18 |
| abaqus   | 9623 | stopped  | unknown  | no      | 2026-05-18 |
+----------+------+----------+----------+---------+------------+
```

### Actions

```text
> Create domain
  Show detail
  Start
  Stop
  Recreate
  Regenerate files
  Archive remove
  Permanent delete
  Inspect API
  Refresh
  Back
```

### Admin routes

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
```

### User-safe route

```text
GET /lightrag/domains
```

### Inspect fields

- admin route
- domain ID
- manifest path
- storage path
- generated compose path
- last operation
- health response
- Docker operation status

Do not expose secrets.

## 5.6 Jobs

### Default table

```text
+------------+----------------+----------+------------+------------+
| job_id     | kind           | status   | document   | updated    |
+------------+----------------+----------+------------+------------+
| job_77b... | document_ingest | running  | doc_01f... | 13:25      |
| job_88c... | document_ingest | failed   | doc_05b... | 13:35      |
+------------+----------------+----------+------------+------------+
```

### Routes

```text
GET /jobs
GET /jobs/{job_id}
POST /jobs/{job_id}/retry
```

### Inspect fields

- full job ID
- full document ID
- error message
- metadata
- route
- retry response payload

## 5.7 Observability

### Default view

Keep two compact panels:

```text
Recent Query Logs
Recent Audit Logs
```

Do not show every metadata field by default.

### Routes

```text
GET /admin/query-logs
GET /admin/audit-logs
```

### Inspect fields

- log ID
- user ID
- route/action
- query/mode
- metadata
- timestamps

## 5.8 Health / Readiness

### Default table

```text
+-------------------------+----------+-----------------------------+
| check                   | status   | detail                      |
+-------------------------+----------+-----------------------------+
| API health              | ok       | /health                     |
| API readiness           | ready    | /health/readiness           |
| database                | ok       | reachable                   |
| storage                 | ok       | .data writable              |
| redis / worker          | warn     | worker heartbeat missing    |
| LightRAG runtime        | ok       | fatigue healthy             |
| LightRAG deploy control | ok       | docker reachable            |
+-------------------------+----------+-----------------------------+
```

Only show rows backed by real routes or real backend payloads.

## 5.9 Backend Gaps

### Default table

```text
+----------------------+-----------------------------+----------+-----------+
| capability           | missing route               | priority | note      |
+----------------------+-----------------------------+----------+-----------+
| document search      | GET /documents/search?q=    | medium   | planned   |
| conversations        | GET /conversations          | low      | future    |
| users admin          | GET /users                  | medium   | planned   |
+----------------------+-----------------------------+----------+-----------+
```

Rule:

```text
Backend gaps must never render as fake success.
```


---

# 6. Error, Backend Gap, and Security UX

## 6.1 Standard Error Panel

```text
ERROR

code:    forbidden
message: Admin access required
route:   POST /admin/documents/upload
status:  403
time:    31 ms

Next:
- Sign in as an admin.
- Check current role with /auth/me.
```

## 6.2 Error Panel Must Include

- backend error code
- backend message
- method and route
- HTTP status
- latency if available
- practical next action

## 6.3 Error Panel Must Not Include

- access token
- password
- raw request headers
- API keys
- stack traces by default
- local filesystem secrets
- Docker secrets
- LightRAG API key

## 6.4 Connection Error

```text
ERROR

code:    connection_failed
message: Could not connect to backend
route:   GET /auth/me
backend: http://127.0.0.1:8000

Next:
- Start the backend.
- Check --api-base-url.
- Confirm saved session backend URL.
```

## 6.5 Auth Error

```text
ERROR

code:    auth_required
message: Sign in via context-engine first
route:   GET /documents
status:  401

Next:
- Go to Login.
```

## 6.6 Forbidden Error

```text
ERROR

code:    forbidden
message: Admin access required
route:   GET /admin/documents
status:  403

Next:
- Check current role in session summary.
- Sign in as an admin.
```

## 6.7 Backend Gap Panel

```text
BACKEND GAP

Capability: Document text search
Current route: none
Suggested route: GET /documents/search?q=
Status: not_supported_by_backend

Next:
- Implement backend route first.
- Add cli/services wrapper.
- Add TUI screen.
- Add tests.
```

## 6.8 Sensitive Output Rules

- Never print bearer tokens.
- Never print passwords.
- Never print API keys.
- Never display raw request headers unless sanitized.
- Display file upload path only when useful; avoid leaking unnecessary absolute paths by default.
- For LightRAG domain screens, do not display secrets from generated env files.
- For Docker errors, show stderr summary but scrub secrets.

## 6.9 Raw JSON Redaction

Before rendering raw JSON:

- redact fields named `token`, `access_token`, `password`, `api_key`, `secret`, `authorization`
- truncate huge `content`, `full_text`, `embedding`, and raw graph arrays by default
- include a note when fields are truncated or redacted

Example:

```json
{
  "access_token": "[REDACTED]",
  "content": "[TRUNCATED 12450 chars]"
}
```


---

# 7. Traceability Matrix

| TUI Screen | User Intent | Backend Route | Default View | Inspect View | Admin? | Backend Gap? |
|---|---|---|---|---|---:|---:|
| Login | Authenticate | `POST /auth/login` | Email/password form | Request shape, status, saved-session summary | No | No |
| Session | Current identity | `GET /auth/me` | User email/role | Raw user JSON | No | No |
| Documents | Browse ready docs | `GET /documents` | Document table | Full IDs, response count, raw JSON | No | No |
| Document Detail | View one doc | `GET /documents/{id}` | Metadata summary | Full metadata JSON | No | No |
| Document Structure | View outline | `GET /documents/{id}/structure` | Tree/table | Full structure JSON | No | No |
| Document Page | View page text | `GET /documents/{id}/pages/{page}` | Page text excerpt | Full page payload | No | No |
| Documents Admin Actions | Upload/list/rebuild/reingest/delete | `/admin/documents...` | Admin action menu | Route/payload/status | Yes | No |
| Retrieval | Retrieve evidence | `POST /retrieve` | Query form/result table | Request JSON, evidence IDs, raw response | No | No |
| Retrieval Compare | Compare modes | repeated `POST /retrieve` | Mode comparison table | Per-mode payload/status/errors | No | No |
| Graphs | Graph labels/summary | `/graphs`, `/graph/label/...` | Labels/summary table | Params, node/edge counts, raw JSON | No | No |
| LightRAG Domains | Deploy/manage domains | `/admin/lightrag/domains...` | Domain table/actions | Manifest path, compose path, Docker status | Yes | No |
| Domain Selector | Choose query domain | `GET /lightrag/domains` | Domain dropdown/list | User-safe domain payload | No | No |
| Jobs | Monitor ingestion jobs | `GET /jobs` | Jobs table | Full job metadata/raw JSON | Yes | No |
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


---

# 8. TDD Implementation Plan

## Slice 1: Root Menu Cleanup

### Tests

- root menu includes `Documents`
- root menu includes `Retrieval`
- root menu includes `Graphs`
- root menu includes `LightRAG Domains` for admin
- root menu does not include `LightRAG Graphs`
- root menu does not include `Admin Documents`
- root menu does not include LightRAG domain CRUD actions

### Files

```text
cli/tui/screens/main_menu.py
cli/tui/state.py
tests/test_cli_tui.py
tests/test_cli_screen_renderers.py
```

## Slice 2: Shared Screen Chrome

### Tests

- screen footer shows route/status/latency
- local-only screen says local only
- backend gap screen says backend gap
- key hints include `I`, `J`, `F`, `R`, `B`, `Q`

### Files

```text
cli/tui/renderers/
cli/tui/styles.py
tests/test_cli_screen_renderers.py
```

## Slice 3: API Inspect Drawer

### Tests

- GET inspect drawer renders method/route/status/latency
- POST inspect drawer renders request JSON
- multipart inspect drawer hides bytes
- DELETE inspect drawer shows confirmation/payload
- secrets are redacted

### Files

```text
cli/tui/renderers/inspect.py
cli/tui/screens/*
tests/test_cli_screen_renderers.py
```

## Slice 4: Raw JSON Viewer

### Tests

- raw JSON pretty-prints response
- token/password/api_key fields are redacted
- long content fields are truncated
- full IDs can be toggled

### Files

```text
cli/tui/renderers/json_view.py
tests/test_cli_screen_renderers.py
```

## Slice 5: Documents/Admin Consolidation

### Tests

- root does not show `Admin Documents`
- Documents screen shows admin actions for admin
- Documents screen hides admin actions for normal user
- admin actions call `/admin/documents...`
- browse actions call `/documents...`

### Files

```text
cli/tui/screens/documents.py
cli/services/documents.py
cli/services/admin_documents.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 6: Retrieval Debug Visibility

### Tests

- retrieval screen includes query/mode/top_k/domain/document filters
- inspect mode shows exact request payload
- result table shows engine/score/pages/section/document
- raw JSON available

### Files

```text
cli/tui/screens/retrieval.py
cli/services/query.py
cli/query_payload.py
tests/test_cli_query_payload.py
tests/test_cli_tui.py
```

## Slice 7: Graphs Rename

### Tests

- root menu shows `Graphs`
- graph screen title is `GRAPHS`
- graph service still calls `/graphs` and `/graph/label/...`

### Files

```text
cli/tui/screens/graphs.py
cli/services/lightrag.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 8: LightRAG Domains Nested CRUD

### Tests

- root has only `LightRAG Domains`
- LightRAG Domains screen includes create/start/stop/recreate/remove
- TUI service calls `/admin/lightrag/domains...`
- permanent delete requires typed confirmation

### Files

```text
cli/tui/screens/lightrag_domains.py
cli/services/lightrag_domains.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 9: Health / Readiness

### Tests

- health screen calls `/health`
- readiness screen calls `/health/readiness`
- status rows show check/status/detail
- unavailable checks render warning, not fake OK

### Files

```text
cli/tui/screens/health.py
cli/services/health.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 10: Backend Gaps Cleanup

### Tests

- backend gaps show capability/missing route/priority/note
- unsupported capabilities do not call fake backend success routes
- gap screen recommends backend-first implementation path

### Files

```text
cli/tui/screens/backend_gaps.py
cli/screens/planned.py
tests/test_cli_tui.py
```

## Slice 11: Documentation Update

Update:

```text
docs/cli_docs/tui_ux.md
docs/cli_docs/frontend_traceability.md
docs/cli_docs/api-contract.md
docs/cli_docs/ascii_render_conformance.md
```

## Slice 12: Test Commands

Run:

```bash
pytest tests/test_cli_tui.py tests/test_cli_services.py tests/test_cli_screen_renderers.py -q
```

If ASCII conformance tests exist:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

## Acceptance Criteria

- Default screens are clean and not cluttered.
- Every API-backed screen has inspect mode.
- Raw JSON is available but hidden by default.
- Root menu is capability-based.
- Admin actions are nested, not duplicated at root.
- Graphs label no longer leaks LightRAG implementation.
- LightRAG domain CRUD is under LightRAG Domains.
- TUI stays a thin client over backend API.
- Tests prove route mapping and render behavior.


---

# 9. Coding Agent Prompt

```markdown
# Task: Refine Context Engine Rich TUI for Backend/API Debugging Without Clutter

You are a senior CLI/TUI UX designer and senior Python engineer.

Refine the current `context_engine` terminal UI so it remains clean for operators but becomes more useful as a backend/API testing console.

## Current Direction

Supported entrypoints:

```text
context-engine
context-tui
```

Current CLI architecture:

```text
cli/launcher.py
cli/config.py
cli/credentials.py
cli/api_client.py
cli/services/
cli/tui/
cli/main.py  # compatibility delegate only
```

Do not design around legacy `ragcli` as the main UX.

## Core UX Rule

```text
Default view = clean operator summary.
Inspect/debug view = backend/API visibility.
```

Do not show every request/response field on the default screen.

## Required Root Menu

Admin:

```text
Documents
Retrieval
Graphs
LightRAG Domains
Jobs
Observability
Health / Readiness
Backend Gaps
Logout
Quit
```

Normal user:

```text
Documents
Retrieval
Graphs
Health / Readiness
Logout
Quit
```

## Required Global Keys

```text
↑/↓  Move
Enter Select
R    Refresh
I    Inspect API
J    Raw JSON
F    Toggle full IDs
D    Debug details, admin only
B    Back
Q    Quit
```

## Required UX Features

### 1. Shared screen chrome

Every API-backed screen should show a compact footer:

```text
Route: POST /retrieve    Status: 200    Time: 63 ms
```

### 2. API Inspect drawer

Pressing `I` should show:

- method
- route
- query params or payload
- status code
- latency
- response summary
- selected IDs

### 3. Raw JSON viewer

Pressing `J` should show pretty-printed backend response JSON.

Rules:

- redact tokens/passwords/API keys
- truncate large fields
- do not show file bytes
- do not show stack traces by default

### 4. Full ID toggle

Pressing `F` toggles between truncated and full IDs.

### 5. Debug mode

Pressing `D` shows backend debug payload only if returned and user is admin.

## Required Screen Changes

### Documents

Unify `Documents` and `Admin Documents`.

Root should show only:

```text
Documents
```

Inside Documents:

```text
Browse Ready Documents
View Detail
View Structure
View Page
Admin Actions   # admin only
```

Admin Actions:

```text
Upload Document
List All Documents
Rebuild structure / Reingest LightRAG / Refresh LightRAG status
Delete Document
```

### Retrieval

Default screen should show:

- query
- mode
- LightRAG domain
- top_k
- document filter
- general fallback
- debug requested

Result table:

```text
# | engine | score | pages | document | section
```

Inspect mode shows request payload and evidence IDs.

### Graphs

Rename:

```text
LightRAG Graphs -> Graphs
```

Do not rename backend routes in this task.

Still call:

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

### LightRAG Domains

Root should show only:

```text
LightRAG Domains
```

Inside:

```text
List Domains
Create Domain
Show Detail
Start
Stop
Recreate
Regenerate Files
Archive Remove
Permanent Delete
```

TUI must not call Docker. It calls `cli/services/lightrag_domains.py`, which calls backend API through `ApiClient`.

### Jobs

Default columns:

```text
job_id | kind | status | document | updated
```

Inspect mode shows full IDs, metadata, errors, route, retry payload.

### Observability

Keep default minimal:

```text
Recent Query Logs
Recent Audit Logs
```

Inspect selected logs for metadata.

### Health / Readiness

Show status table:

```text
check | status | detail
```

Do not fake health checks that backend does not provide.

### Backend Gaps

Show:

```text
capability | missing backend route | priority | note
```

Unsupported features must not fake success.

## Sensitive Output Rules

Never print:

- access tokens
- passwords
- API keys
- Authorization headers
- backend secrets
- LightRAG secrets
- Docker secrets

## Tests First

Add/update tests for:

1. root menu cleanup
2. shared screen footer
3. inspect drawer
4. raw JSON redaction
5. full ID toggle
6. Documents/Admin consolidation
7. Retrieval inspect payload
8. Graphs rename
9. LightRAG Domains nested CRUD
10. Health/readiness screen
11. Backend gap screen

Run:

```bash
pytest tests/test_cli_tui.py tests/test_cli_services.py tests/test_cli_screen_renderers.py -q
```

If available:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

## Do Not Do

- Do not add backend business logic to TUI.
- Do not call Docker from TUI.
- Do not call LightRAG directly from TUI.
- Do not show raw JSON by default.
- Do not show stack traces by default.
- Do not merge backend routes in this UI task.
- Do not revive legacy Typer command tree as the main UX.

## Acceptance Criteria

The work is complete when:

- root menu is clean and capability-based
- default screens are uncluttered
- API inspect mode exists for API-backed screens
- raw JSON is available on demand
- full IDs are toggleable
- admin actions are nested and role-aware
- backend gaps are honest
- route/status/latency is visible compactly
- TUI remains a thin API client
- tests cover the new behavior
```
