# context-engine TUI Documents Upload UX Fix

## Purpose

This document converts the current Documents-screen UX gap into an implementation-ready plan and coding-agent prompt.

The current `context-engine` Documents screen shows a command suggestion:

```text
Next:
  context-engine admin documents upload --file ./manual.pdf
```

This is useful in a command reference, but not user-friendly inside an interactive TUI. A TUI user should be able to select an upload action, enter a file path, submit the upload, and see the result without leaving the TUI.

---

## 1. Current Problem

The current screen roughly shows:

```text
DOCUMENTS

No documents found

Next:
  context-engine admin documents upload --file ./manual.pdf

No documents found.

Actions: Up/Down Select | Enter Open | Ctrl+R Refresh | B Back | Q Quit
```

## UX Gaps

| Gap | Why It Is a Problem | Required Fix |
| --- | --- | --- |
| Upload is shown only as a command suggestion | User has no place to enter a file path inside the TUI | Add selectable `Upload document` action |
| `Enter Open` is shown with no documents | There is nothing to open | Hide document-open actions when the list is empty |
| `No documents found` appears twice | Screen feels broken or duplicated | Render one clear empty state |
| Upload is not selectable | User cannot continue the workflow | Add an empty-state action menu |
| No file path input | User cannot provide `./manual.pdf` | Add upload form screen |
| Upload is admin-only | Normal users may not have permission | Let backend authorize and render `403` |
| Previous terminal output remains above screen | TUI behaves like appended output, not screen app | Clear/redraw each screen |
| No upload result state | User does not know what happened after upload | Add upload success/error result screens |

---

## 2. Design Goal

The Documents screen should behave like an interactive screen, not a command reference page.

Replace:

```text
Next:
  context-engine admin documents upload --file ./manual.pdf
```

With:

```text
> Upload document
  Refresh
  Back
  Quit
```

Then provide a real upload form:

```text
UPLOAD DOCUMENT

File path:
  [ ./manual.pdf                     ]

Actions:
  Enter  Submit upload
  Tab    Next field
  B      Back
  Q      Quit
```

---

## 3. Required Empty Documents Screen

When `GET /documents` returns an empty list, render:

```text
DOCUMENTS

No documents found.

> Upload document
  Refresh
  Back
  Quit

Actions:
  Up/Down  Select
  Enter    Choose
  Ctrl+R   Refresh
  B        Back
  Q        Quit
```

Do not show:

```text
Enter Open
```

when there are no documents.

Do not duplicate:

```text
No documents found.
```

---

## 4. Documents Screen With Existing Documents

When documents exist, keep document selection behavior and add an upload shortcut:

```text
DOCUMENTS

+---------+----------------------+----------+
| ID      | Filename             | Status   |
+---------+----------------------+----------+
| > doc_1 | manual.pdf           | ready    |
|   doc_2 | guide.pdf            | indexing |
+---------+----------------------+----------+

Actions:
  Up/Down  Select document
  Enter    Open selected document
  U        Upload document
  Ctrl+R   Refresh
  B        Back
  Q        Quit
```

Rules:

- `Enter Open` is shown only when at least one document exists.
- `U Upload document` is available from the Documents screen.
- Upload should open the same upload form used by the empty-state action.

---

## 5. Upload Flow

## 5.1 Upload Form Screen

```text
UPLOAD DOCUMENT

File path:
  [ ./manual.pdf                     ]

Actions:
  Enter  Submit upload
  Tab    Next field
  B      Back
  Q      Quit
```

The user must be able to type or paste a file path.

The form must support:

- text input for file path
- path editing
- Back
- Quit
- Submit
- local file-exists validation before backend upload
- clean error if file does not exist
- backend error rendering if upload fails

---

## 5.2 Upload API Rule

The upload flow must reuse the existing backend contract:

```bash
context-engine admin documents upload --file PATH
```

which maps to:

```text
POST /admin/documents/upload
```

Do not create a separate TUI-only upload implementation.

The TUI should call the same API client method or command-layer operation used by normal CLI upload.

---

## 5.3 Admin Permission Rule

Do not infer admin permission locally.

When the user submits upload:

1. Validate the local file path exists.
2. Attempt the backend upload request.
3. If the backend returns `403`, render a clean forbidden screen.
4. Do not hide or fake admin behavior based only on local state.

Forbidden screen:

```text
FORBIDDEN

forbidden: Admin permission required.

The backend rejected this upload request.

Actions:
  B  Back
  Q  Quit
```

---

## 5.4 Invalid File Path Screen

If the user enters a path that does not exist, do not call the backend.

```text
UPLOAD ERROR

file_not_found: Could not find file:
  ./manual.pdf

> Edit file path
  Back
  Quit
```

Rules:

- Backend upload route must not be called.
- User can return to the form and edit the path.
- User can go back or quit.

---

## 5.5 Successful Upload Screen With Local Job

If upload succeeds and the backend returns a local indexing job:

```text
UPLOAD COMPLETE

+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| File           | manual.pdf                 |
| Document ID    | doc_123                    |
| Status         | uploaded                   |
| Job ID         | job_456                    |
+----------------+----------------------------+

> View job status
  Return to documents
  Upload another document
  Quit

Actions:
  Up/Down  Select
  Enter    Choose
  B        Back
  Q        Quit
```

Recommended action behavior:

| Action | Behavior |
| --- | --- |
| View job status | Push Job Status screen for returned `job_id` |
| Return to documents | Refresh and return to Documents screen |
| Upload another document | Reset to Upload Document form |
| Quit | Exit TUI |

---

## 5.6 Successful Upload Screen With LightRAG Forwarding

If upload succeeds but LightRAG forwarding returns no local job:

```text
UPLOAD COMPLETE

+------------------------+----------------------------+
| Field                  | Value                      |
+------------------------+----------------------------+
| File                   | manual.pdf                 |
| Document ID            | doc_123                    |
| Status                 | forwarded_to_lightrag      |
| Local job ID           | none                       |
+------------------------+----------------------------+

> Return to documents
  Upload another document
  View LightRAG labels
  Quit
```

Rules:

- Do not crash when `job_id` is `null`.
- Do not show `View job status` when there is no job.
- Offer LightRAG-related next steps only when the response indicates LightRAG forwarding.

---

## 6. Screen Clearing Requirement

The TUI must behave like a screen app, not a scrolling log.

Before rendering each active screen:

```python
console.clear()
```

Screen loop:

```text
clear -> render active screen -> read key -> update state -> clear -> render next screen
```

Do not implement the TUI as repeated `print()` calls that append output.

---

## 7. Navigation Rules

Use a screen stack:

```text
Documents
  -> Upload Document
    -> Upload Complete
    -> Upload Error
  -> Document Detail
```

Rules:

| Key | Behavior |
| --- | --- |
| Up/Down | Move selected item |
| Enter | Choose selected action |
| U | Open upload form from Documents screen |
| Ctrl+R | Refresh Documents |
| B | Back |
| Q | Quit |

---

## 8. Suggested Implementation Files

```text
cli/
  tui/
    screens/
      documents.py
      upload_document.py
      upload_result.py
      error.py
    navigation.py
    widgets.py
    styles.py
```

Reuse existing modules where possible:

```text
cli/api/client.py
cli/auth/credentials.py
cli/renderers/tables.py
cli/screens/documents.py
```

---

## 9. Design Rules

- Keep backend business rules in the backend.
- Keep upload authorization in the backend.
- Keep TUI upload logic focused on collecting a file path and calling the API.
- Do not print tokens.
- Do not print passwords.
- Do not echo request headers.
- Use ASCII tables only.
- Keep the TUI mostly black and white.
- Do not duplicate CLI command behavior.
- Do not create a fake local upload flow.
- Do not call LightRAG directly.
- Do not infer admin permissions locally.

---

# 10. TDD Plan

Build this in vertical slices. Do not write all tests first.

## Slice 1: Empty documents screen has actionable menu

Test:

```text
test_empty_documents_screen_shows_upload_refresh_back_quit
```

Given:

- `GET /documents` returns `[]`

Assert:

- output contains `No documents found.`
- output contains `Upload document`
- output contains `Refresh`
- output contains `Back`
- output does not contain `Enter Open`
- output does not duplicate `No documents found.`

---

## Slice 2: Selecting Upload opens file path form

Test:

```text
test_empty_documents_upload_action_opens_file_path_form
```

Assert:

- pressing Enter on `Upload document` clears screen
- output contains `UPLOAD DOCUMENT`
- output contains `File path`
- output contains `Submit upload`

---

## Slice 3: Invalid file path shows local error

Test:

```text
test_upload_form_invalid_file_path_shows_error_without_backend_call
```

Assert:

- backend upload route is not called
- output contains `file_not_found`
- output lets user edit path or go back

---

## Slice 4: Valid file path calls admin upload route

Test:

```text
test_upload_form_valid_file_path_calls_admin_upload_route
```

Assert:

- backend route called: `POST /admin/documents/upload`
- multipart field is `file`
- output contains `UPLOAD COMPLETE`

---

## Slice 5: Upload success with job shows job action

Test:

```text
test_upload_success_with_job_shows_view_job_status_action
```

Assert:

- output contains document ID
- output contains job ID
- output contains `View job status`

---

## Slice 6: Upload success without job handles LightRAG forwarding

Test:

```text
test_upload_success_without_job_handles_lightrag_forwarding
```

Assert:

- no crash when `job_id` is null
- output says `Local job ID none`
- output suggests returning to documents or viewing LightRAG labels

---

## Slice 7: Backend 403 renders forbidden screen

Test:

```text
test_upload_backend_403_renders_forbidden_screen
```

Assert:

- backend request is attempted
- output contains `FORBIDDEN`
- output contains `Admin permission required`
- no local admin inference

---

## Slice 8: Existing documents screen includes upload shortcut

Test:

```text
test_documents_screen_with_documents_includes_upload_shortcut
```

Assert:

- documents table is shown
- output contains `U Upload document`
- `Enter Open` is only shown when selectable documents exist

---

## Slice 9: TUI clears screen between states

Test:

```text
test_upload_flow_replaces_previous_screen_instead_of_appending_output
```

Assert:

- after navigating from Documents to Upload, final screen buffer contains `UPLOAD DOCUMENT`
- final screen buffer does not contain stale deploy example commands
- final screen buffer does not contain old duplicated empty-state text

---

# 11. Coding Agent Prompt

Use the following prompt with your coding agent.

```markdown
# Prompt: Fix TUI Documents Empty-State UX and Add Interactive Upload Flow

You are a senior Python CLI/TUI engineer. Improve the current `context-engine` Documents screen so it behaves like a real interactive TUI screen, not a command reference page.

## Current Problem

The current Documents screen shows:

```text
DOCUMENTS

No documents found

Next:
  context-engine admin documents upload --file ./manual.pdf

No documents found.

Actions: Up/Down Select | Enter Open | Ctrl+R Refresh | B Back | Q Quit
```

This is not user-friendly because:

1. The screen tells the user to run an upload command, but gives no place to enter a file path.
2. `Enter Open` is shown even though there are no documents to open.
3. `No documents found` appears twice.
4. The upload action is not selectable.
5. The user cannot complete the upload workflow inside the TUI.
6. Upload is an admin action, but the screen does not explain whether the user has permission.
7. The previous CLI/deploy output appears above the TUI, so the screen may not be clearing cleanly.
8. The empty state does not guide the user through the next logical action.

## Goal

Update the TUI so the Documents screen has a proper empty-state workflow.

When no documents exist, show an interactive menu, not a plain command suggestion.

## Required Empty Documents Screen

When `GET /documents` returns an empty list, render:

```text
DOCUMENTS

No documents found.

> Upload document
  Refresh
  Back
  Quit

Actions:
  Up/Down  Select
  Enter    Choose
  Ctrl+R   Refresh
  B        Back
  Q        Quit
```

Do not show `Enter Open` when there are no documents.

Do not show duplicate `No documents found.` text.

## Upload Flow Requirement

When the user selects `Upload document`, show an upload form:

```text
UPLOAD DOCUMENT

File path:
  [ ./manual.pdf                     ]

Actions:
  Enter  Submit upload
  Tab    Next field
  B      Back
  Q      Quit
```

The user must be able to type or paste a file path.

The form should support:

- text input for file path
- Back
- Quit
- Submit
- local validation that the path exists before making the API call
- useful error if file does not exist
- backend error rendering if upload fails

## Upload API Rule

The upload flow must reuse the existing backend contract:

```bash
context-engine admin documents upload --file PATH
```

which maps to:

```text
POST /admin/documents/upload
```

Do not create a separate TUI-only upload implementation.

The TUI should call the same API client method or command-layer operation used by normal CLI upload.

## Admin Permission Rule

Do not infer admin permission locally.

When the user selects upload:

1. Attempt the backend upload request.
2. If the backend returns `403`, render a clean forbidden screen.
3. Do not hide or fake admin behavior based only on local state.

## Successful Upload Screen

If upload succeeds and the backend returns a local indexing job:

```text
UPLOAD COMPLETE

+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| File           | manual.pdf                 |
| Document ID    | doc_123                    |
| Status         | uploaded                   |
| Job ID         | job_456                    |
+----------------+----------------------------+

> View job status
  Return to documents
  Upload another document
  Quit
```

If upload succeeds but LightRAG forwarding returns no local job:

```text
UPLOAD COMPLETE

+------------------------+----------------------------+
| Field                  | Value                      |
+------------------------+----------------------------+
| File                   | manual.pdf                 |
| Document ID            | doc_123                    |
| Status                 | forwarded_to_lightrag      |
| Local job ID           | none                       |
+------------------------+----------------------------+

> Return to documents
  Upload another document
  View LightRAG labels
  Quit
```

## Invalid File Path Screen

If the user enters a path that does not exist, do not call the backend.

Show:

```text
UPLOAD ERROR

file_not_found: Could not find file:
  ./manual.pdf

> Edit file path
  Back
  Quit
```

## Documents Screen With Existing Documents

When documents exist, keep document selection behavior:

```text
DOCUMENTS

+---------+----------------------+----------+
| ID      | Filename             | Status   |
+---------+----------------------+----------+
| > doc_1 | manual.pdf           | ready    |
|   doc_2 | guide.pdf            | indexing |
+---------+----------------------+----------+

Actions:
  Up/Down  Select document
  Enter    Open selected document
  U        Upload document
  Ctrl+R   Refresh
  B        Back
  Q        Quit
```

Add `U Upload document` as a shortcut.

## Screen Clearing Requirement

The screenshot shows deploy/command instructions still visible above the Documents screen. Fix the TUI so active screens do not appear below old terminal output.

Before rendering each TUI screen:

```python
console.clear()
```

The TUI must behave like a screen app:

```text
clear -> render active screen -> read key -> update state -> clear -> render next screen
```

Do not implement the TUI as repeated `print()` calls that append output.

## Navigation Rules

Use a screen stack:

```text
Documents
  -> Upload Document
    -> Upload Complete
    -> Upload Error
  -> Document Detail
```

Rules:

- `Enter` opens selected action.
- `U` opens upload from Documents screen.
- `B` goes back.
- `Q` quits.
- `Ctrl+R` refreshes Documents.
- Successful upload should allow returning to Documents and refreshing the list.

## TDD Requirements

Build this in vertical slices. Do not write all tests first.

### Slice 1: Empty documents screen has actionable menu

Test:

```text
test_empty_documents_screen_shows_upload_refresh_back_quit
```

### Slice 2: Selecting Upload opens file path form

Test:

```text
test_empty_documents_upload_action_opens_file_path_form
```

### Slice 3: Invalid file path shows local error

Test:

```text
test_upload_form_invalid_file_path_shows_error_without_backend_call
```

### Slice 4: Valid file path calls admin upload route

Test:

```text
test_upload_form_valid_file_path_calls_admin_upload_route
```

### Slice 5: Upload success with job shows job action

Test:

```text
test_upload_success_with_job_shows_view_job_status_action
```

### Slice 6: Upload success without job handles LightRAG forwarding

Test:

```text
test_upload_success_without_job_handles_lightrag_forwarding
```

### Slice 7: Backend 403 renders forbidden screen

Test:

```text
test_upload_backend_403_renders_forbidden_screen
```

### Slice 8: Existing documents screen includes upload shortcut

Test:

```text
test_documents_screen_with_documents_includes_upload_shortcut
```

### Slice 9: TUI clears screen between states

Test:

```text
test_upload_flow_replaces_previous_screen_instead_of_appending_output
```

## Implementation Notes

Keep the interface simple and deep.

Suggested files:

```text
cli/tui/screens/documents.py
cli/tui/screens/upload_document.py
cli/tui/screens/upload_result.py
cli/tui/screens/error.py
```

Reuse existing modules:

```text
cli/api/client.py
cli/auth/credentials.py
cli/renderers/tables.py
cli/screens/documents.py
```

## Design Rules

- Keep backend business rules in the backend.
- Keep upload authorization in the backend.
- Keep TUI upload logic focused on collecting a file path and calling the API.
- Do not print tokens.
- Do not print passwords.
- Do not echo request headers.
- Use ASCII tables only.
- Keep the TUI mostly black and white.
- Do not duplicate CLI command behavior.
- Do not create a fake local upload flow.
```
