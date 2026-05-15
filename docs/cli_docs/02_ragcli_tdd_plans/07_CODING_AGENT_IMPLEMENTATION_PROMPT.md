# Coding Agent Prompt: Implement ragcli Screen UX + Lightweight TUI Using TDD

## Role

You are a senior Python software engineer using test-driven development.

Write clean, boring, maintainable code that a junior developer can follow.

## Context

This repo contains `ragcli`, a thin command-line client for the Context Engine backend.

The CLI:

- authenticates with the backend
- stores backend base URL and access token
- calls FastAPI routes
- renders human output or stable JSON
- mirrors current and future frontend capabilities
- must not invent behavior that the backend does not support

The CLI is also a test harness for future frontend screens.

## Objective

Implement a lightweight screen-oriented CLI UX and optional black-and-white TUI.

The result should include:

1. Better human output for existing commands.
2. ASCII table rendering.
3. Shared screen/result models.
4. `ragcli ui` lightweight TUI.
5. Guided flows for retrieval comparison and admin upload/dashboard if feasible.
6. Explicit backend-gap rendering for unsupported planned commands.
7. Stable JSON output.

## Critical constraints

Do not violate these:

- Do not call LightRAG directly from the CLI.
- Do not infer admin permissions locally.
- Do not print access tokens.
- Do not print passwords.
- Do not echo request headers.
- Do not break `--output json`.
- Do not fake backend behavior for planned commands.
- Unsupported commands must return `not_supported_by_backend`.
- Use ASCII tables.
- Keep the TUI mostly black-and-white.
- Reserve color only for semantic meaning.

## TDD rules

Use vertical red-green-refactor slices.

Do not write all tests first.

For each behavior:

```text
RED: write one failing behavior test
GREEN: implement minimal code to pass
REFACTOR: clean only while tests are green
```

Tests should verify behavior through public interfaces.

Mock only system boundaries:

- backend HTTP API
- keyring/credential storage
- file system where needed

Do not mock internal modules you control.

## Implementation phases

## Phase 1 — Human screen renderers

Add or improve:

```text
cli/renderers/
  tables.py
  errors.py
  documents.py
  retrieval.py
  lightrag.py
  admin_documents.py
  jobs.py
  observability.py
  planned.py
```

Start with one tracer bullet:

```text
ragcli documents list
```

Behavior:

- human output renders a screen-like document library
- table uses ASCII borders
- JSON output remains unchanged

Tests:

```text
test_documents_list_human_output_is_screen_like_ascii_table
test_documents_list_json_shape_is_unchanged
```

Then implement renderers for retrieval, query, LightRAG, admin documents, jobs, logs, and planned gaps.

## Phase 2 — Screen models

Add:

```text
cli/screens/
  models.py
  documents.py
  retrieval.py
  lightrag.py
  admin_documents.py
  jobs.py
  observability.py
  planned.py
```

Use simple dataclasses:

```python
@dataclass(frozen=True)
class ScreenAction:
    label: str
    command: str
    disabled: bool = False
    reason: str | None = None

@dataclass(frozen=True)
class ScreenSection:
    title: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    text: str | None = None

@dataclass(frozen=True)
class ScreenResult:
    title: str
    api_group: str
    summary: dict[str, Any] = field(default_factory=dict)
    sections: list[ScreenSection] = field(default_factory=list)
    actions: list[ScreenAction] = field(default_factory=list)
    raw: Any = None
```

Keep the model small.

Do not create a full UI framework.

## Phase 3 — TUI

Add:

```text
ragcli ui
```

Suggested modules:

```text
cli/commands/ui.py
cli/tui/app.py
cli/tui/menu.py
cli/tui/styles.py
cli/tui/screens/
```

TUI main menu:

```text
CONTEXT ENGINE

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

TUI tests:

```text
test_ui_command_is_registered
test_tui_starts_renders_main_menu_and_exits
test_tui_documents_screen_renders_document_library
test_tui_backend_gaps_screen_lists_planned_unsupported_surfaces
```

TUI must reuse the same screen builders as command mode.

## Phase 4 — Guided flows

Add only if the first three phases are green.

Candidate flows:

```bash
ragcli retrieval compare --query "reset procedure"
ragcli admin documents upload-flow --file ./manual.pdf
ragcli admin dashboard
```

Each flow must compose real backend routes.

## Visual style

Use a centralized style file:

```text
cli/tui/styles.py
```

Example:

```python
API_GROUP_STYLES = {
    "auth": "blue",
    "documents": "cyan",
    "retrieval": "green",
    "lightrag": "magenta",
    "admin": "yellow",
    "jobs": "yellow",
    "observability": "blue",
    "gaps": "dim",
}
```

Use color sparingly.

Use ASCII table boxes.

If using Rich:

```python
from rich import box
Table(box=box.ASCII)
```

Avoid:

```python
Table(box=box.ROUNDED)
Panel(..., border_style="bright_magenta")
```

## Acceptance criteria

Done means:

- Existing tests pass.
- New behavior tests pass.
- JSON output is stable.
- Human output is screen-like.
- TUI starts and exits.
- TUI tables are ASCII.
- TUI is mostly monochrome.
- Unsupported commands/screens show backend gaps.
- No secrets are printed.
- No direct LightRAG calls.
- Code remains small, boring, and readable.
