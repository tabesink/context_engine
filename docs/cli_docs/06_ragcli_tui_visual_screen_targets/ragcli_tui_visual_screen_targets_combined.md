# ragcli TUI Visual UX Screen Target Documentation



---

# File: 00_README.md

# ragcli TUI Visual Screen Targets

This bundle contains downloadable markdown documentation for improving the `ragcli ui` visual UX.

Focus:
- clean full-screen TUI views
- no stale deploy/startup banner inside active TUI screens
- semantic color usage
- ASCII tables
- compact action footers
- useful default selections
- upload-result screens that guide the user to the next step
- screen examples the coding agent can implement against

## Files

1. `01_VISUAL_UX_PRINCIPLES.md`
2. `02_UPLOAD_FLOW_SCREEN_TARGETS.md`
3. `03_DOCUMENTS_AND_RETRIEVAL_SCREEN_TARGETS.md`
4. `04_ADMIN_JOBS_LIGHTRAG_ERROR_SCREEN_TARGETS.md`
5. `05_CODING_AGENT_VISUAL_IMPLEMENTATION_PROMPT.md`

## Key rule

The TUI must behave like a screen application:

```text
clear -> render active screen -> read key -> update state -> clear -> render next screen
```

Do not append new TUI output under old terminal output.

## Color policy

Use mostly black-and-white text.

Color should be reserved for:
- success
- warning
- error
- selected row/action
- disabled/backend-gap states
- subtle API group accent

Use ASCII tables only.



---

# File: 01_VISUAL_UX_PRINCIPLES.md

# ragcli TUI Visual UX Principles

## Objective

Improve `ragcli ui` so it feels like a clean terminal application, not raw command output.

The current UI is functional, but it can be improved by:

- clearing stale startup text
- adding clear screen hierarchy
- using semantic status labels
- truncating long IDs in tables
- making recommended next actions obvious
- using compact action footers
- using color only where it helps

## Current Visual Problems

A screen like this is functional but not ideal:

```text
CLI ready.
API base URL: http://127.0.0.1:8010

Example commands:
  .venv\Scripts\ragcli.exe --api-base-url http://127.0.0.1:8010 --help
  .venv\Scripts\ragcli.exe --api-base-url http://127.0.0.1:8010 login
  .venv\Scripts\ragcli.exe --api-base-url http://127.0.0.1:8010 ui

UPLOAD COMPLETE

+----------------------------------------------------------+
| Field       | Value                                      |
+----------------------------------------------------------+
| File        | Resume_2026_working.pdf                    |
| Document ID | 54d1d557-f9f1-41b9-9776-b9b7308d2905       |
| Status      | uploaded                                   |
| Job ID      | b40dc5e9-b05b-481e-a8ef-9f80ec50de48      |
+----------------------------------------------------------+

  View job status
  Return to documents
  Upload another document
> Quit

Actions:
  Up/Down  Select
  Enter    Choose
  B        Back
  Q        Quit
```

Problems:

| Gap | Current Problem | Improvement |
| --- | --- | --- |
| Stale banner visible | Startup/deploy text remains above TUI | Clear screen before active TUI render |
| Weak hierarchy | `UPLOAD COMPLETE` is plain | Use breadcrumb + success state |
| Long UUIDs | Table becomes hard to scan | Truncate in summary table |
| Bad default action | `Quit` is selected | Default to recommended next step |
| Tall footer | Help consumes too much vertical space | Use compact footer |
| Raw-table feel | User sees fields but not a summary | Add one-line success explanation |

## Visual Design Rules

### 1. Clear before every active screen render

The TUI must not appear underneath old command output.

Use this loop conceptually:

```text
clear -> render active screen -> read key -> update state -> clear -> render next screen
```

### 2. Use breadcrumb titles

Prefer:

```text
ADMIN DOCUMENTS / UPLOAD
RETRIEVAL / CONTEXT
JOBS / STATUS
```

Instead of isolated titles like:

```text
UPLOAD COMPLETE
STATUS
RESULT
```

### 3. Use semantic state labels

Use simple status markers:

```text
[SUCCESS] Upload complete
[WARN] Indexing in progress
[ERROR] Job failed
[ERROR] Forbidden
```

If Unicode is reliable in your target terminal, `[OK]` can be replaced with `✓`, but `[SUCCESS]`, `[WARN]`, and `[ERROR]` are more portable.

### 4. Keep color semantic

Suggested color mapping:

| Element | Suggested Color |
| --- | --- |
| Success label | green |
| Warning label | yellow |
| Error label | red |
| Selected action | cyan or reverse video |
| Disabled state | dim gray |
| Admin accent | yellow |
| LightRAG accent | magenta |
| Retrieval accent | green |
| Normal text | terminal default |

Do not use color as decoration.

### 5. Use ASCII tables

Good:

```text
+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| File        | manual.pdf                           |
+-------------+--------------------------------------+
```

Avoid Unicode box drawing:

```text
┌─────────────┬────────────────────┐
│ Field       │ Value              │
└─────────────┴────────────────────┘
```

### 6. Truncate long IDs in summary tables

Prefer:

```text
54d1d557...b7308d2905
```

Instead of:

```text
54d1d557-f9f1-41b9-9776-b9b7308d2905
```

Provide a `Show full IDs` action when needed.

### 7. Use compact footers

Prefer:

```text
Up/Down Select | Enter Choose | B Back | Q Quit
```

Instead of:

```text
Actions:
  Up/Down  Select
  Enter    Choose
  B        Back
  Q        Quit
```

### 8. Default selection should be useful

After upload with job:

```text
> View job status
```

After upload without job:

```text
> Return to documents
```

Avoid defaulting to:

```text
> Quit
```

## Implementation Checklist

```text
[ ] Clear stale startup/deploy text before TUI render
[ ] Use breadcrumb title on every screen
[ ] Add semantic status line
[ ] Use ASCII tables
[ ] Truncate long UUIDs in summary tables
[ ] Add Show full IDs action where needed
[ ] Select recommended next action by default
[ ] Use compact footer
[ ] Use color only for semantic meaning
[ ] Keep normal command-mode JSON unchanged
```



---

# File: 02_UPLOAD_FLOW_SCREEN_TARGETS.md

# Upload Flow Screen Targets

These are the target ASCII screen views for the `ragcli ui` upload flow.

Use these as inspiration for implementation and tests.

## 1. Upload Document Form

```text
ADMIN DOCUMENTS / UPLOAD

Select a file to upload into the document corpus.

File path:
  [ C:\Users\admin\Documents\manual.pdf                         ]

Validation:
  File will be checked before upload.

> Submit upload
  Clear path
  Back
  Quit

Tab Next Field | Enter Choose | B Back | Q Quit
```

## 2. Upload Form With Missing Path Error

```text
ADMIN DOCUMENTS / UPLOAD

[ERROR] File not found

The file path below does not exist:

  C:\Users\admin\Documents\manual.pdf

File path:
  [ C:\Users\admin\Documents\manual.pdf                         ]

> Edit file path
  Back
  Quit

Enter Choose | B Back | Q Quit
```

## 3. Upload Complete With Local Job

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

Implementation notes:

- Default selected action should be `View job status`.
- Use green for `[SUCCESS]`.
- Use yellow/admin accent for breadcrumb if desired.
- Truncate long IDs in the table.
- Full UUIDs should be available through `Show full IDs`.

## 4. Upload Complete With LightRAG Forwarding

```text
ADMIN DOCUMENTS / UPLOAD

[SUCCESS] Upload complete

Resume_2026_working.pdf was uploaded and forwarded to LightRAG.
No local indexing job was created.

+----------------+--------------------------------------+
| Field          | Value                                |
+----------------+--------------------------------------+
| File           | Resume_2026_working.pdf              |
| Status         | forwarded_to_lightrag                |
| Document ID    | 54d1d557...b7308d2905                |
| Local Job ID   | none                                 |
+----------------+--------------------------------------+

Recommended next step:
> Return to documents
  View LightRAG labels
  Upload another document
  Show full IDs
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

Implementation notes:

- Do not crash when `job_id` is null.
- Default selected action should be `Return to documents`.
- Offer `View LightRAG labels` if graph/label routes are available.

## 5. Upload Complete Full ID Details

```text
ADMIN DOCUMENTS / UPLOAD / DETAILS

Full identifiers

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| Document ID | 54d1d557-f9f1-41b9-9776-b9b7308d2905 |
| Job ID      | b40dc5e9-b05b-481e-a8ef-9f80ec50de48 |
+-------------+--------------------------------------+

> Back to upload result
  Copy document ID
  Copy job ID
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

If clipboard support is not available, omit copy actions and just show full IDs.

## 6. Upload Forbidden

```text
ADMIN DOCUMENTS / UPLOAD

[ERROR] Forbidden

The backend rejected this upload request.

+--------+----------------------------+
| Field  | Value                      |
+--------+----------------------------+
| Code   | forbidden                  |
| Status | 403                        |
| Reason | Admin permission required  |
+--------+----------------------------+

> Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

Implementation notes:

- Do not infer admin status locally.
- Attempt the backend request and render backend `403`.
- Do not print token, password, or request headers.

## 7. Upload Connection Failure

```text
ADMIN DOCUMENTS / UPLOAD

[ERROR] Upload failed

Could not connect to backend.

Backend:
  http://127.0.0.1:8010

> Retry upload
  Edit file path
  Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## TDD Targets

```text
test_upload_result_screen_does_not_show_stale_startup_output
test_upload_success_defaults_to_view_job_status_when_job_exists
test_upload_success_without_job_defaults_to_return_documents
test_upload_result_truncates_long_document_and_job_ids
test_upload_result_uses_compact_footer
test_upload_result_view_job_status_opens_job_screen
test_upload_result_return_to_documents_opens_documents_screen
test_upload_result_upload_another_opens_upload_form
test_upload_forbidden_renders_backend_403
```



---

# File: 03_DOCUMENTS_AND_RETRIEVAL_SCREEN_TARGETS.md

# Documents and Retrieval Screen Targets

These are the target ASCII views for document browsing and retrieval.

## 1. Main Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: admin@example.com

> Documents
  Retrieval
  LightRAG Graphs
  Admin Documents
  Jobs
  Observability
  Backend Gaps
  Logout
  Quit

Up/Down Select | Enter Choose | Q Quit
```

## 2. Documents Empty State

```text
DOCUMENTS

No documents found.

Recommended next step:
> Upload document
  Refresh
  Back
  Quit

Up/Down Select | Enter Choose | Ctrl+R Refresh | B Back | Q Quit
```

Do not show command hints like:

```text
Next:
  ragcli admin documents upload --file ./manual.pdf
```

Inside the TUI, the user should receive actions, not instructions to leave the TUI.

## 3. Documents With Existing Documents

```text
DOCUMENTS

+---------+--------------------------+----------+-------+------------+
| ID      | Filename                 | Status   | Pages | Updated    |
+---------+--------------------------+----------+-------+------------+
| > doc_1 | bed_manual.pdf           | ready    | 42    | 2026-05-14 |
|   doc_2 | mattress_specs.pdf       | indexing | --    | 2026-05-14 |
|   doc_3 | service_guide.pdf        | failed   | --    | 2026-05-13 |
+---------+--------------------------+----------+-------+------------+

Selected:
  bed_manual.pdf

Actions:
  Enter Open selected document
  R     Retrieve from selected document
  U     Upload document
  Ctrl+R Refresh
  B     Back
  Q     Quit
```

Notes:

- Show `Enter Open` only when there are documents.
- Keep `U Upload document` available for admin users or allow backend to enforce permission.
- Do not duplicate `No documents found`.

## 4. Document Detail

```text
DOCUMENTS / DETAIL

bed_manual.pdf

+-------------+--------------------------+
| Field       | Value                    |
+-------------+--------------------------+
| Document ID | doc_1                    |
| Status      | ready                    |
| Pages       | 42                       |
| Updated     | 2026-05-14               |
+-------------+--------------------------+

> View structure
  Open page
  Retrieve from this document
  Reindex document
  Delete document
  Back

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 5. Retrieval Input Screen

```text
RETRIEVAL

Ask a question against the document corpus.

Query:
  [ how do I reset the pendant?                                  ]

Mode:
  > auto
    semantic
    navigation
    hybrid

Top K:
  [ 5 ]

Document filter:
  none

> Run retrieval
  Generate answer
  Compare modes
  Back

Tab Next Field | Up/Down Select | Enter Choose | B Back | Q Quit
```

## 6. Retrieved Context Screen

```text
RETRIEVAL / CONTEXT

Query:
  how do I reset the pendant?

+-----+----------+-------------+-------+--------+---------------------+
| #   | Source   | Engine      | Score | Pages  | Section             |
+-----+----------+-------------+-------+--------+---------------------+
| > 1 | doc_123  | navigation  | 0.84  | 12     | Troubleshooting     |
|   2 | doc_456  | semantic    | 0.77  | 4      | Pendant Controls    |
|   3 | doc_123  | hybrid      | 0.72  | 14-15  | Controller Recovery |
+-----+----------+-------------+-------+--------+---------------------+

Selected Evidence [1]

Document:
  doc_123

Section:
  Troubleshooting

Text:
  To reset the pendant, disconnect power, wait 30 seconds, reconnect the
  power cable, and follow the pendant reset sequence.

Actions:
  Up/Down Select evidence
  Enter   Open source page
  A       Generate answer
  M       Change retrieval mode
  B       Back
  Q       Quit
```

## TDD Targets

```text
test_empty_documents_screen_shows_upload_refresh_back_quit
test_empty_documents_screen_does_not_show_enter_open
test_empty_documents_screen_does_not_duplicate_no_documents_found
test_documents_screen_with_documents_includes_upload_shortcut
test_documents_screen_shows_enter_open_only_when_documents_exist
test_retrieval_screen_renders_query_mode_top_k_and_actions
test_retrieved_context_screen_renders_evidence_table_and_selected_detail
```



---

# File: 04_ADMIN_JOBS_LIGHTRAG_ERROR_SCREEN_TARGETS.md

# Admin, Jobs, LightRAG, and Error Screen Targets

These screens support admin workflows, job inspection, graph exploration, and errors.

## 1. Job Status After Upload

```text
JOBS / STATUS

[WARN] Indexing in progress

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| Job ID      | b40dc5e9...9f80ec50de48              |
| Type        | index_document                       |
| Status      | running                              |
| Document ID | 54d1d557...b7308d2905                |
| Started     | 2026-05-14 20:41                     |
+-------------+--------------------------------------+

Progress:
  Parsing document and building retrieval index.

> Refresh status
  Return to documents
  Back
  Quit

Enter Choose | Ctrl+R Refresh | B Back | Q Quit
```

## 2. Job Failed

```text
JOBS / STATUS

[ERROR] Job failed

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| Job ID      | b40dc5e9...9f80ec50de48              |
| Type        | index_document                       |
| Status      | failed                               |
| Document ID | 54d1d557...b7308d2905                |
+-------------+--------------------------------------+

Error:
  Could not parse document. The file may be corrupted or unsupported.

Recommended next step:
> Retry job
  Upload another document
  Return to documents
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 3. LightRAG Labels

```text
LIGHTRAG / LABELS

+-----+------------------------+-------+
| #   | Label                  | Count |
+-----+------------------------+-------+
| > 1 | installation           | 42    |
|   2 | reset                  | 35    |
|   3 | pendant                | 28    |
|   4 | controller             | 24    |
|   5 | troubleshooting        | 21    |
+-----+------------------------+-------+

Selected:
  installation

> Open graph
  Search labels
  Refresh
  Back
  Quit

Up/Down Select | Enter Choose | Ctrl+R Refresh | B Back | Q Quit
```

## 4. LightRAG Disabled

```text
LIGHTRAG

[ERROR] LightRAG unavailable

The backend returned:

  LightRAG is disabled.

This CLI does not connect to LightRAG directly.
Enable LightRAG in the backend configuration, then refresh.

> Refresh
  Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 5. Backend Gaps

```text
BACKEND GAPS

These capabilities are planned but do not have backend routes yet.

+----------------+-------------------------------+--------------------------+
| Capability     | CLI Command                   | Status                   |
+----------------+-------------------------------+--------------------------+
| Chat           | ragcli chat                   | not_supported_by_backend |
| Users          | ragcli users list             | not_supported_by_backend |
| Conversations  | ragcli conversations list     | not_supported_by_backend |
| Runs           | ragcli runs status            | not_supported_by_backend |
| Approvals      | ragcli runs approvals list    | not_supported_by_backend |
+----------------+-------------------------------+--------------------------+

> View command details
  Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 6. Forbidden / Admin Required

```text
ADMIN DOCUMENTS

[ERROR] Forbidden

The backend rejected this request.

+--------+----------------------------+
| Field  | Value                      |
+--------+----------------------------+
| Code   | forbidden                  |
| Status | 403                        |
| Reason | Admin permission required  |
+--------+----------------------------+

> Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 7. Connection Failure

```text
CONNECTION FAILED

[ERROR] Could not connect to backend

Backend:
  http://127.0.0.1:8010

Try:
  1. Confirm the backend is running.
  2. Check the API base URL.
  3. Restart the CLI after the backend is available.

> Retry
  Change API URL
  Quit

Up/Down Select | Enter Choose | Q Quit
```

## 8. Loading Screen

```text
LOADING

Fetching documents...

Backend:
  http://127.0.0.1:8010

Please wait.
```

## 9. Login Screen

```text
CONTEXT ENGINE LOGIN

Backend:
  http://127.0.0.1:8010

Email:
  [ admin@example.com                                             ]

Password:
  [ ********                                                     ]

> Login
  Change backend URL
  Quit

Tab Next Field | Enter Choose | Q Quit
```

## 10. Logged Out Screen

```text
LOGGED OUT

Your local CLI session has been cleared.

> Login again
  Quit

Up/Down Select | Enter Choose | Q Quit
```

## TDD Targets

```text
test_job_status_running_shows_warning_and_refresh_action
test_job_failed_shows_retry_as_default_action
test_lightrag_labels_screen_uses_ascii_table
test_lightrag_disabled_renders_backend_error
test_backend_gaps_screen_lists_not_supported_commands
test_forbidden_screen_renders_backend_403
test_connection_failure_screen_suggests_retry_and_change_api_url
test_login_screen_masks_password
test_logged_out_screen_offers_login_again
```



---

# File: 05_CODING_AGENT_VISUAL_IMPLEMENTATION_PROMPT.md

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

