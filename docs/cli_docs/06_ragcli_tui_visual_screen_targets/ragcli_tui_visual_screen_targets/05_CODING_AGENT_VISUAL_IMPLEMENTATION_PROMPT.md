# Coding Agent Prompt: Improve ragcli TUI Visual UX

You are a senior Python CLI/TUI engineer and product-minded UX designer.

Improve the `ragcli ui` visual design so it feels like a polished terminal application, not raw command output.

## Current problem

The current upload result screen is functional but has UX issues:

- stale startup/deploy text remains visible above the active TUI screen
- success state does not stand out
- long UUIDs make the table hard to scan
- default selected action is `Quit`
- action footer is too tall
- no one-line success explanation
- screen feels like raw terminal output rather than a TUI page

## Goal

Implement the visual targets from these docs:

- `01_VISUAL_UX_PRINCIPLES.md`
- `02_UPLOAD_FLOW_SCREEN_TARGETS.md`
- `03_DOCUMENTS_AND_RETRIEVAL_SCREEN_TARGETS.md`
- `04_ADMIN_JOBS_LIGHTRAG_ERROR_SCREEN_TARGETS.md`

## Hard requirements

1. Clear before every TUI screen render.
2. Never show stale deploy/startup text inside active TUI screens.
3. Use breadcrumb titles.
4. Use `[SUCCESS]`, `[WARN]`, and `[ERROR]` state labels.
5. Use color only for semantic meaning.
6. Use ASCII tables only.
7. Truncate long UUIDs in summary tables.
8. Add `Show full IDs` when full IDs matter.
9. Default to the recommended next action.
10. Use compact action footers.
11. Keep backend business rules in the backend.
12. Do not infer admin permissions locally.
13. Do not call LightRAG directly.
14. Do not print tokens, passwords, or request headers.
15. Do not change command-mode JSON output.

## Suggested color rules

Centralize styles in one place.

```python
SUCCESS = "green"
WARNING = "yellow"
ERROR = "red"
SELECTED = "cyan"
MUTED = "dim"
ADMIN_ACCENT = "yellow"
LIGHTRAG_ACCENT = "magenta"
RETRIEVAL_ACCENT = "green"
```

Use normal terminal color for most text.

## Suggested helper functions

Add small, reusable helpers:

```python
def truncate_id(value: str, prefix: int = 8, suffix: int = 12) -> str:
    ...

def render_key_footer(items: list[tuple[str, str]]) -> str:
    ...

def render_ascii_table(rows: list[dict[str, str]]) -> RenderableType:
    ...
```

Keep interfaces small and implementation deep.

## Primary target screen

The upload-with-job result should look like:

```text
ADMIN DOCUMENTS / UPLOAD

[SUCCESS] Upload complete

Resume_2026_working.pdf was uploaded successfully.
An indexing job was created and is ready to inspect.

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| File        | Resume_2026_working.pdf              |
| Status      | uploaded                             |
| Document ID | 54d1d557...b7308d2905                |
| Job ID      | b40dc5e9...9f80ec50de48              |
+-------------+--------------------------------------+

Recommended next step:
> View job status
  Return to documents
  Upload another document
  Show full IDs
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## TDD implementation order

Use vertical slices. Do not write all tests first.

### Slice 1: Screen clear removes stale startup text

Test:

```text
test_upload_result_screen_does_not_show_stale_startup_output
```

Assert:

- final screen contains `ADMIN DOCUMENTS / UPLOAD`
- final screen contains `Upload complete`
- final screen does not contain `CLI ready`
- final screen does not contain `Example commands`

### Slice 2: Success screen uses useful default action

Test:

```text
test_upload_success_defaults_to_view_job_status_when_job_exists
```

Assert:

- selected action is `View job status`
- `Quit` is not selected by default

### Slice 3: Upload without job defaults to return documents

Test:

```text
test_upload_success_without_job_defaults_to_return_documents
```

Assert:

- selected action is `Return to documents`
- screen does not crash when `job_id` is null

### Slice 4: Long IDs are truncated

Test:

```text
test_upload_result_truncates_long_document_and_job_ids
```

Assert:

- full UUID is not shown in summary table
- shortened ID is shown
- `Show full IDs` action exists

### Slice 5: Compact footer

Test:

```text
test_upload_result_uses_compact_footer
```

Assert output contains:

```text
Up/Down Select | Enter Choose | B Back | Q Quit
```

Assert output does not contain the old tall footer:

```text
Actions:
  Up/Down
  Enter
```

### Slice 6: Semantic success state

Test:

```text
test_upload_result_uses_success_state_label
```

Assert:

- output contains `[SUCCESS] Upload complete`
- success style is applied through public render model or styled output

### Slice 7: Navigation still works

Tests:

```text
test_upload_result_view_job_status_opens_job_screen
test_upload_result_return_to_documents_opens_documents_screen
test_upload_result_upload_another_opens_upload_form
test_upload_result_show_full_ids_opens_details_screen
```

## Acceptance criteria

The implementation is done when:

- active TUI screen no longer shows stale startup/deploy text
- upload complete screen has clear success hierarchy
- color is semantic and restrained
- long IDs are truncated in summary tables
- full IDs remain accessible
- default action is useful
- compact footer is used
- ASCII tables are used
- navigation still works
- command-mode JSON remains unchanged
