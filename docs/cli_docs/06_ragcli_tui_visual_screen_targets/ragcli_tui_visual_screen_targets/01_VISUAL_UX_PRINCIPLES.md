# context-engine TUI Visual UX Principles

## Objective

Improve `context-engine` so it feels like a clean terminal application, not raw command output.

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
API base URL: http://127.0.0.1:8000

Example commands:
  .venv\Scripts\context-engine.exe --api-base-url http://127.0.0.1:8000 --help
  .venv\Scripts\context-engine.exe --api-base-url http://127.0.0.1:8000 login
  .venv\Scripts\context-engine.exe --api-base-url http://127.0.0.1:8000 ui

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
