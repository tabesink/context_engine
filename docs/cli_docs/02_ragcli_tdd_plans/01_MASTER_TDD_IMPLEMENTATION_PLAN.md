# Master TDD Implementation Plan: context-engine Screen UX + Lightweight TUI

## Objective

Evolve `context-engine` from a thin command client into a clean API-mirrored testing interface for the Context Engine backend and future frontend.

The result should support:

1. Existing direct CLI commands.
2. Better human output that looks like lightweight “screens.”
3. Shared screen/result models.
4. Optional lightweight TUI via `context-engine`.
5. Explicit backend-gap screens for planned unsupported capabilities.
6. Stable JSON output for automation.

## Architecture target

```text
cli/
  api/
    client.py
    errors.py

  auth/
    credentials.py
    session.py

  commands/
    auth.py
    documents.py
    query.py
    lightrag.py
    admin_documents.py
    jobs.py
    logs.py
    planned.py
    ui.py

  payloads/
    query_payload.py

  screens/
    models.py
    session.py
    documents.py
    retrieval.py
    lightrag.py
    admin_documents.py
    jobs.py
    observability.py
    planned.py

  renderers/
    base.py
    tables.py
    errors.py
    session.py
    documents.py
    retrieval.py
    lightrag.py
    admin_documents.py
    jobs.py
    observability.py
    planned.py

  flows/
    retrieval_compare.py
    upload_document.py
    refresh_status_document.py

  tui/
    app.py
    menu.py
    styles.py
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

## Design principles

### 1. API-first

Every supported command or TUI action must call the backend API through the existing API client.

Do not create local behavior that bypasses the backend.

### 2. Same behavior, multiple renderers

A direct command and a TUI screen should eventually share the same lower-level operation:

```text
fetch data → build screen/result model → render as human/JSON/TUI
```

### 3. JSON is stable

Human and TUI output can improve.

JSON output must remain stable and script-safe.

### 4. Mostly black-and-white TUI

The TUI should use:

- default terminal foreground/background
- ASCII tables
- minimal color
- color only for semantic categories, errors, warnings, success, disabled states

### 5. Senior architecture, junior-readable code

Prefer:

- small functions
- simple dataclasses
- obvious file names
- limited abstraction
- behavior tests through public interfaces

Avoid:

- deep inheritance
- framework-heavy architecture
- clever dynamic dispatch
- testing private methods
- mocking internal modules

## Phases

## Phase 1 — Human screen renderers

Goal:

Improve human command output while preserving JSON.

Deliverables:

- ASCII table helper
- consistent error renderer
- document renderers
- retrieval renderers
- graph renderers
- admin/jobs/log renderers
- unsupported planned-command renderer

Primary test style:

- CLI runner tests through public commands.
- Mock only the HTTP boundary.
- Assert stable JSON exactly.
- Assert human output contains key labels, tables, actions, and no secrets.

## Phase 2 — Shared screen/result models

Goal:

Create lightweight screen/result models that can be reused by CLI and TUI.

Deliverables:

- `ScreenResult`
- `ScreenSection`
- `ScreenAction`
- screen builders for documents, retrieval, graphs, admin, jobs, observability, planned gaps

Primary test style:

- Test public screen builder functions.
- Pass simple fake API responses.
- Verify resulting public screen model fields.
- Do not test private formatting helpers.

## Phase 3 — Lightweight TUI

Goal:

Add `context-engine`, a black-and-white terminal UI over the same API-backed screens.

Deliverables:

- TUI app entrypoint
- main menu
- screen navigation
- documents screen
- retrieval screen
- LightRAG screen
- admin documents screen
- jobs screen
- observability screen
- backend gaps screen
- smoke tests

Primary test style:

- Start app in test mode.
- Verify main menu renders.
- Verify each screen calls the same API/screen builder layer.
- Verify unsupported features show backend-gap state.
- Keep TUI tests minimal and behavior-focused.

## Phase 4 — Guided one-shot flows

Goal:

Add workflow helpers that represent future frontend flows.

Candidate flows:

- `context-engine retrieval compare --query "..."`
- `context-engine admin documents upload-flow --file ./manual.pdf`
- `context-engine admin dashboard`
- optional `context-engine screen documents`
- optional `context-engine screen graph`

Primary test style:

- Test end-to-end CLI behavior with mocked backend responses.
- Verify calls are made to expected public backend routes.
- Verify failure paths render actionable errors.
- Verify JSON remains stable if JSON is supported for a flow.

## Phase 5 — Frontend traceability docs

Goal:

Add docs that map CLI/TUI/API capabilities to future frontend screens.

Deliverables:

- `docs/cli_docs/frontend_traceability.md`
- `docs/cli_docs/tui_ux.md`
- `docs/cli_docs/tdd_implementation_status.md`

## Acceptance criteria

The implementation is acceptable when:

- All existing command behavior tests pass.
- New renderer tests pass.
- JSON output is unchanged for existing supported commands.
- `context-engine` opens and exits cleanly.
- TUI uses ASCII tables and minimal semantic color.
- Unsupported planned commands and screens show `not_supported_by_backend`.
- No tokens/passwords are printed.
- CLI still does not call LightRAG directly.
- Code remains easy for a junior developer to trace.
