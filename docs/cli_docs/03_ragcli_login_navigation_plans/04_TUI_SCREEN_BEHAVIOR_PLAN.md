# TUI Screen Behavior Plan

## Visual rules

The TUI should be mostly black-and-white.

Color is reserved for semantic meaning only:

| Purpose | Color use |
| --- | --- |
| Error | red |
| Warning | yellow |
| Success | green |
| Disabled/backend gap | dim/gray |
| API group accent | optional and subtle |

Avoid:

- decorative colors
- gradients
- emojis
- animations
- Unicode box drawing
- heavy panels

Use ASCII tables.

```text
+---------+------------+--------+
| ID      | Filename   | Status |
+---------+------------+--------+
| doc_123 | manual.pdf | ready  |
+---------+------------+--------+
```

If using Rich:

```python
from rich import box
Table(box=box.ASCII)
```

## Screen list

### 1. Login screen

Purpose:

- Authenticate from inside TUI.

Keys:

| Key | Behavior |
| --- | --- |
| Tab | Move email/password focus |
| Enter | Submit |
| Q | Quit |

### 2. Main menu screen

Options:

```text
Documents
Retrieval
LightRAG Graphs
Admin Documents
Jobs
Observability
Backend Gaps
Logout
Quit
```

Keys:

| Key | Behavior |
| --- | --- |
| Up/Down | Move selection |
| Enter | Open selected option |
| Q | Quit |

### 3. Documents screen

Purpose:

- Show document library using `GET /documents`.

Keys:

| Key | Behavior |
| --- | --- |
| Up/Down | Select document |
| Enter | Open document detail |
| R | Retrieval scoped to selected document |
| B | Back |
| Q | Quit |

Output:

```text
DOCUMENTS

+---------+------------+--------+
| ID      | Filename   | Status |
+---------+------------+--------+
| doc_123 | manual.pdf | ready  |
+---------+------------+--------+
```

### 4. Document detail screen

Purpose:

- Show metadata for selected document using `GET /documents/{document_id}`.

Options:

```text
Structure
Page Viewer
Retrieve from this document
Back
```

### 5. Retrieval screen

Purpose:

- Test retrieval/answer/query endpoints.

Fields:

- query text
- mode: `auto`, `semantic`, `navigation`, `hybrid`
- top_k
- optional document filter

Actions:

```text
Retrieve
Answer
Compare Modes
Back
```

Rules:

- Compare modes must only use supported query/retrieve APIs.
- Debug is displayed only if backend returns it.
- Do not fake debug for non-admin users.

### 6. LightRAG screen

Purpose:

- Explore graph labels and graph neighborhood via backend proxy routes.

Options:

```text
Labels List
Popular Labels
Search Labels
Graph By Label
Back
```

Rules:

- Do not call LightRAG directly.
- Render backend disabled-service errors as error screens.

### 7. Admin documents screen

Purpose:

- Admin document management.

Options:

```text
Upload
Index
Reindex
Delete
Back
```

Rules:

- Do not check admin locally.
- Send request and render backend 403 if normal user lacks permission.

### 8. Jobs screen

Purpose:

- Show indexing jobs.

Keys:

| Key | Behavior |
| --- | --- |
| Up/Down | Select job |
| Enter | Job detail |
| R | Retry failed selected job |
| B | Back |
| Q | Quit |

### 9. Observability screen

Options:

```text
Audit Logs
Query Logs
Back
```

### 10. Backend gaps screen

Purpose:

- Show planned/unsupported surfaces without pretending they work.

Example:

```text
BACKEND GAPS

+----------------+------------------------------+-------------+
| Capability     | CLI Command                  | Status      |
+----------------+------------------------------+-------------+
| Chat           | context-engine chat                  | backend gap |
| Users          | context-engine users list            | backend gap |
| Conversations  | context-engine conversations list    | backend gap |
+----------------+------------------------------+-------------+

These commands must return not_supported_by_backend until backend routes exist.
```

## Empty states

Example:

```text
DOCUMENTS

No documents found.

Actions:
  R Refresh
  B Back
  Q Quit
```

## Error screens

Example:

```text
ERROR

auth_required: Run `context-engine login` first.

Actions:
  B Back
  Q Quit
```

## Loading states

Use simple loading text, not animation-heavy behavior:

```text
LOADING

Fetching documents...
```

## Acceptance criteria

- All screens use the same navigation conventions.
- All screens clear/redraw on transition.
- Tables use ASCII borders.
- Color is minimal.
- Backend errors are rendered clearly.
- Unsupported surfaces appear as backend gaps, not fake local features.
