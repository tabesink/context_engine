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
Route: POST /query/retrieve    Status: 200    Time: 63 ms
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
Index / Reindex
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
