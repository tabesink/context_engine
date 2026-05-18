# Phase 1 TDD Plan: Human Screen Renderers

## Objective

Improve human output for existing API-backed commands without changing command behavior or JSON output.

This phase should make the CLI feel like a set of frontend-aligned “screens” while keeping the CLI thin.

## Scope

Commands to improve:

```text
login
logout
auth me
documents list
documents show
documents structure
documents page
documents retrieve
documents answer
query
lightrag labels list
lightrag labels popular
lightrag labels search
lightrag graphs show
admin documents upload
admin documents list
admin documents index
admin documents reindex
admin documents delete
admin audit-logs list
admin query-logs list
jobs list
jobs status
jobs retry
planned unsupported commands
```

## Visual style

Use ASCII tables.

Good:

```text
+---------+------------+--------+
| ID      | Filename   | Status |
+---------+------------+--------+
| doc_123 | manual.pdf | ready  |
+---------+------------+--------+
```

Avoid Unicode box drawing.

Use monochrome output by default.

Color is allowed only for:

- error
- warning
- success
- disabled/backend gap
- small API group accent

## Target modules

```text
cli/renderers/
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
```

## Public interfaces

Keep renderer interfaces small.

Example:

```python
def render_human(result: Any, *, console: Console) -> None:
    ...

def render_json(result: Any, *, console: Console) -> None:
    ...

def render_error(error: CliError, *, output: Literal["human", "json"], console: Console) -> None:
    ...
```

Better:

```python
def render_documents_list(documents: list[dict[str, Any]], console: Console) -> None:
    ...
```

Avoid over-abstracting early.

## TDD vertical slices

### Slice 1 — ASCII table helper

Behavior:

> A list of dictionaries can be rendered as a portable ASCII table.

RED test:

```text
test_ascii_table_renders_headers_rows_and_ascii_borders
```

Expected behavior:

- output contains `+`
- output contains `|`
- output contains headers
- output contains row values
- output does not contain Unicode box characters such as `┌`, `┬`, `│`

GREEN:

- Implement the smallest `render_ascii_table` helper.
- If using Rich, force `box.ASCII`.

Refactor:

- Keep width handling simple.
- Do not build a custom table engine unless necessary.

---

### Slice 2 — Documents list human renderer

Behavior:

> `context-engine documents list` renders a document library table in human mode.

RED test:

```text
test_documents_list_human_output_is_screen_like_ascii_table
```

Mock boundary:

- HTTP response for `GET /documents`.

Assert:

- command exits `0`
- output includes `Documents`
- output includes document ID and filename
- output includes ASCII table borders
- output suggests next useful commands
- output does not include token/password

GREEN:

- Route human result through `render_documents_list`.

Refactor:

- Extract repeated action footer if duplication appears.

---

### Slice 3 — Documents list JSON remains stable

Behavior:

> `context-engine documents list --output json` returns the existing stable JSON shape.

RED test:

```text
test_documents_list_json_shape_is_unchanged
```

Assert exact JSON shape:

```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "manual.pdf",
      "status": "ready"
    }
  ]
}
```

GREEN:

- Ensure renderer branch respects `--output json`.

Refactor:

- Do not let human renderer mutate the raw response.

---

### Slice 4 — Retrieval human renderer

Behavior:

> Retrieval output shows query, requested mode, selected engine when present, evidence blocks, source metadata, and next commands.

RED test:

```text
test_documents_retrieve_human_output_shows_evidence_and_debug_when_backend_returns_it
```

Mock boundary:

- `POST /query/retrieve`.

Assert:

- output includes query
- output includes evidence text
- output includes document ID/source
- output includes page range if present
- output includes debug only if backend response contains it

GREEN:

- Implement `render_retrieval_result`.

Refactor:

- Extract evidence-block rendering.

---

### Slice 5 — Query/answer human renderer

Behavior:

> Query/answer output shows final answer and source evidence in a clean screen-like layout.

Tests:

```text
test_query_human_output_shows_answer_and_sources
test_documents_answer_human_output_shows_answer_and_sources
```

Assert:

- answer is visible
- sources are visible
- no headers/tokens printed
- JSON mode still unchanged

---

### Slice 6 — LightRAG labels renderers

Behavior:

> LightRAG label lists render as ASCII tables and mention backend-disabled errors when returned by backend.

Tests:

```text
test_lightrag_labels_popular_human_output_uses_ascii_table
test_lightrag_disabled_backend_error_is_rendered_actionably
```

Mock boundary:

- `GET /graph/label/popular`
- backend error for disabled LightRAG

Assert:

- output contains label/count fields
- output includes actionable backend error message
- CLI does not call LightRAG directly

---

### Slice 7 — Graph neighborhood renderer

Behavior:

> `lightrag graphs show` renders graph summary and recommends JSON export for visualization.

Test:

```text
test_lightrag_graph_show_human_output_summarizes_nodes_edges
```

Assert:

- label shown
- node count shown
- edge count shown
- top labels shown if available
- recommends `--output json`

---

### Slice 8 — Admin document upload renderer

Behavior:

> Upload output shows document ID, job ID if present, LightRAG metadata if present, and next commands.

Tests:

```text
test_admin_upload_human_output_shows_local_indexing_job
test_admin_upload_human_output_handles_lightrag_forwarded_upload_without_job
```

Assert:

- `job_id` shown when present
- no crash when `job_id` is null
- next command suggests jobs status only when job exists
- no token/password output

---

### Slice 9 — Jobs renderer

Behavior:

> Jobs list/status/retry render clear state and failure diagnostics.

Tests:

```text
test_jobs_list_human_output_uses_ascii_table
test_jobs_status_human_output_shows_failed_error_and_retry_action
```

---

### Slice 10 — Admin logs renderer

Behavior:

> Query logs and audit logs render tabular summaries.

Tests:

```text
test_admin_query_logs_human_output_uses_ascii_table
test_admin_audit_logs_human_output_uses_ascii_table
```

---

### Slice 11 — Planned unsupported command renderer

Behavior:

> Unsupported planned commands return explicit `not_supported_by_backend` in human and JSON mode.

Tests:

```text
test_planned_command_human_output_returns_not_supported_by_backend
test_planned_command_json_output_returns_structured_error
```

Expected human:

```text
not_supported_by_backend: `context-engine chat` needs a backend route first.
```

Expected JSON:

```json
{
  "error": {
    "code": "not_supported_by_backend",
    "message": "`context-engine chat` needs a backend route first.",
    "status": 1
  }
}
```

## Refactor checklist after green

- Remove duplicated table setup.
- Keep renderers dumb.
- Keep output branching simple.
- Do not move API calls into renderers.
- Do not introduce global state.
- Run full CLI test suite.
