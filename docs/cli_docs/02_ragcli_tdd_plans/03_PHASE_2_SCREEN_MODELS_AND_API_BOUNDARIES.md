# Phase 2 TDD Plan: Screen Models and API Boundaries

## Objective

Introduce lightweight screen/result models that let direct commands and TUI screens share the same behavior.

This prevents TUI code from becoming a second implementation of the CLI.

## Design target

```text
ApiClient → screen builder → renderer
                         ↘ → TUI
```

## Target modules

```text
cli/screens/
  models.py
  session.py
  documents.py
  retrieval.py
  lightrag.py
  admin_documents.py
  jobs.py
  observability.py
  planned.py
```

## Minimal data model

Use simple dataclasses.

```python
from dataclasses import dataclass, field
from typing import Any

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

Keep this model intentionally small.

Do not model a full UI framework.

## API boundary rule

Mock only system boundaries:

- HTTP API client
- file system only for upload file failures
- keyring/session storage when testing credentials

Do not mock internal screen builders or renderers in CLI behavior tests.

## TDD vertical slices

### Slice 1 — Document list screen builder

Behavior:

> Given backend document data, build a document library screen result.

RED test:

```text
test_build_document_library_screen_returns_title_rows_actions_and_raw_data
```

Input:

```python
documents = [
    {"id": "doc_123", "filename": "manual.pdf", "status": "ready"}
]
```

Assert:

- title is `Documents`
- api_group is `documents`
- rows include `doc_123`
- actions include show/retrieve examples
- raw is unchanged input

GREEN:

- Implement `build_document_library_screen`.

Refactor:

- Do not add API calls inside builder.

---

### Slice 2 — Retrieval screen builder

Behavior:

> Given retrieval response, build a retrieval screen with evidence sections and debug section if present.

Test:

```text
test_build_retrieval_screen_includes_evidence_and_optional_debug
```

Assert:

- summary contains query/mode
- evidence section exists
- debug section exists only if backend returned debug

---

### Slice 3 — Graph label screen builder

Behavior:

> Given label response, build a graph label screen.

Tests:

```text
test_build_popular_labels_screen_maps_labels_to_rows
test_build_label_search_screen_maps_results_to_rows
```

---

### Slice 4 — Admin documents screen builder

Behavior:

> Admin document list builds an admin corpus dashboard screen.

Test:

```text
test_build_admin_documents_screen_contains_admin_actions
```

Assert:

- api_group is `admin`
- actions include upload/reingest/refresh-status/delete
- no authorization decision is made locally

---

### Slice 5 — Job screen builder

Behavior:

> Job status builds a job detail screen with retry action only when useful.

Tests:

```text
test_build_job_status_screen_shows_failure_and_retry_action
test_build_job_status_screen_does_not_suggest_retry_for_success
```

---

### Slice 6 — Backend gap screen builder

Behavior:

> Planned unsupported command builds explicit backend gap screen.

Test:

```text
test_build_backend_gap_screen_shows_command_and_missing_backend_route
```

Assert:

- api_group is `gaps`
- disabled action state
- includes command name
- includes `not_supported_by_backend`

---

### Slice 7 — Commands can use screen builders without breaking JSON

Behavior:

> Existing commands render human output through screen builders but JSON output remains raw/stable.

Tests:

```text
test_documents_list_human_uses_screen_result
test_documents_list_json_does_not_include_screen_metadata
```

## Implementation order

1. Add `screens/models.py`.
2. Add document library screen builder.
3. Update one command to use it in human mode only.
4. Verify JSON unchanged.
5. Repeat for retrieval, LightRAG, admin docs, jobs, logs, planned gaps.

## Acceptance criteria

- Screen builders have no side effects.
- Screen builders do not call HTTP.
- Renderers consume screen results.
- TUI can later consume screen results.
- JSON output remains untouched.
- Tests verify behavior through public command/screen builder interfaces.
