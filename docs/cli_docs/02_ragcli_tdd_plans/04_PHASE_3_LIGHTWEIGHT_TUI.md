# Phase 3 TDD Plan: Lightweight Black-and-White TUI

## Objective

Add optional TUI mode:

```bash
ragcli ui
```

The TUI should be a lightweight frontend rehearsal layer over the same API-backed screen builders used by direct commands.

## Non-goals

Do not build:

- a second product
- a complex REPL shell
- local business logic
- direct LightRAG integration
- fake chat/users/runs behavior
- heavy graph visualization in terminal

## Visual design constraints

The TUI must be mostly monochrome.

Use:

- default terminal background
- default terminal foreground
- ASCII tables
- minimal color
- no gradients
- no decorative panels
- no excessive emoji
- no animation-heavy UI

Color is reserved for semantic meaning only:

| Group | Accent |
|---|---|
| auth/session | blue |
| documents | cyan |
| retrieval/query | green |
| lightrag graphs | magenta |
| admin documents | yellow |
| jobs | yellow |
| observability | blue |
| backend gaps | dim/gray |
| errors | red |
| warnings | yellow |
| success | green |

## Recommended dependency

Use one of:

1. Existing Rich/Textual stack if already in the project.
2. Rich-only simple prompt/menu implementation.
3. Textual only if it does not add too much complexity.

Prefer the simplest solution that can:

- show a menu
- show tables
- accept text input
- call existing screen builders
- exit cleanly

## Target modules

```text
cli/commands/ui.py

cli/tui/
  app.py
  menu.py
  styles.py
  keymap.py
  screens/
    session.py
    documents.py
    retrieval.py
    lightrag.py
    admin_documents.py
    jobs.py
    observability.py
    planned.py
```

## TUI main menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8000
Session: admin@example.com

[1] Session
[2] Documents
[3] Retrieval
[4] LightRAG Graphs
[5] Admin Documents
[6] Jobs
[7] Observability
[8] Backend Gaps
[Q] Quit
```

## TDD vertical slices

### Slice 1 — `ragcli ui` command exists

Behavior:

> User can run `ragcli ui --help`.

RED test:

```text
test_ui_command_is_registered
```

Assert:

- command exists
- help text includes "interactive" or "TUI"
- exits 0

GREEN:

- Add command registration only.

---

### Slice 2 — TUI starts and exits

Behavior:

> TUI starts, renders main menu, and exits on quit.

RED test:

```text
test_tui_starts_renders_main_menu_and_exits
```

Test mode:

- Use an injected input event sequence such as `["q"]`.
- Use an in-memory console or captured output.

Assert:

- output contains `CONTEXT ENGINE`
- output contains `Documents`
- output contains `Retrieval`
- output contains `Backend Gaps`
- exits 0

GREEN:

- Implement minimal app loop.

Refactor:

- Extract menu item definitions.

---

### Slice 3 — TUI uses saved session/base URL

Behavior:

> TUI displays saved backend base URL/session summary without exposing token.

Test:

```text
test_tui_session_summary_shows_backend_but_not_token
```

Mock boundary:

- credential/session store.

Assert:

- backend URL shown
- email/user shown if available
- token not shown

---

### Slice 4 — Documents screen

Behavior:

> Documents screen calls the existing document API path and renders a document table.

Test:

```text
test_tui_documents_screen_renders_document_library
```

Mock boundary:

- API client document list method or HTTP boundary.

Assert:

- document ID visible
- filename visible
- ASCII table border visible
- no Unicode box characters

Implementation:

- TUI screen calls the same screen builder as command mode.

---

### Slice 5 — Retrieval screen

Behavior:

> User can enter a query and see retrieval evidence.

Test:

```text
test_tui_retrieval_screen_accepts_query_and_shows_evidence
```

Mock boundary:

- `POST /query/retrieve`.

Input events:

```text
select retrieval
enter query "reset procedure"
submit
quit/back
```

Assert:

- query visible
- evidence visible
- selected mode visible if backend returned it

Keep test focused; do not assert low-level widget internals.

---

### Slice 6 — LightRAG screen

Behavior:

> User can browse popular labels and open graph summary.

Tests:

```text
test_tui_lightrag_popular_labels_screen_renders_labels
test_tui_lightrag_graph_screen_renders_summary_not_full_visualization
```

Assert:

- labels visible
- graph node/edge counts visible
- JSON export hint visible
- no direct LightRAG client used

---

### Slice 7 — Admin documents screen

Behavior:

> Admin screen renders backend authorization response instead of guessing locally.

Tests:

```text
test_tui_admin_documents_screen_renders_documents_for_admin_response
test_tui_admin_documents_screen_renders_backend_403_for_non_admin
```

Mock boundary:

- backend returns success
- backend returns 403

Assert:

- success table shown for success
- `403` shown for forbidden
- no local role check required

---

### Slice 8 — Jobs screen

Behavior:

> Jobs screen renders list and detail summaries.

Tests:

```text
test_tui_jobs_screen_renders_job_queue
test_tui_job_detail_screen_shows_retry_action_for_failed_job
```

---

### Slice 9 — Observability screen

Behavior:

> Observability screen renders query logs and audit logs.

Tests:

```text
test_tui_observability_screen_renders_query_logs
test_tui_observability_screen_renders_audit_logs
```

---

### Slice 10 — Backend gaps screen

Behavior:

> Planned unsupported features appear in the TUI as backend gaps.

Test:

```text
test_tui_backend_gaps_screen_lists_planned_unsupported_surfaces
```

Assert visible:

- chat
- users
- conversations
- runs
- approvals
- corpus publish/rollback/cleanup
- `not_supported_by_backend`

## Acceptance criteria

- `ragcli ui` starts and exits cleanly.
- TUI is mostly black-and-white.
- Tables are ASCII.
- Color is centralized in `tui/styles.py`.
- TUI reuses screen builders.
- TUI does not duplicate command business logic.
- TUI does not call LightRAG directly.
- TUI shows backend gaps explicitly.
- Tests are smoke/behavior tests, not implementation-detail widget tests.
