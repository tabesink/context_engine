# Executive Implementation Plan: `context-engine` Login + Arrow-Key Navigation

## Objective

Implement a lightweight interactive TUI for `context-engine` that behaves like a screen application:

```bash
context-engine
```

The TUI must support:

- Login inside the TUI
- Logout inside the TUI
- Existing session detection
- Expired session fallback to login
- Arrow-key navigation
- Enter-to-select behavior
- Back navigation
- Screen clear/redraw on every transition
- ASCII tables
- Mostly monochrome output
- Backend gap visibility for unsupported planned features

The TUI is not a separate product. It is an interactive, screen-based wrapper around the same backend API contracts used by the existing command CLI.

## Core design thesis

Use this architecture:

```text
Command CLI  -> ApiClient -> Backend
TUI          -> ApiClient -> Backend

Command CLI  -> Screen builders -> Human/JSON renderers
TUI          -> Screen builders -> TUI screen views
```

The TUI should reuse:

- existing `CredentialStore`
- existing `ApiClient`
- existing `/auth/login`, `/auth/me`, and logout session-clearing behavior
- existing request payload builders
- existing backend route contracts
- existing error shape and backend gap semantics

The TUI should not introduce:

- new auth logic
- direct LightRAG calls
- fake backend implementations
- hidden admin checks
- JSON output changes
- complex UI framework abstractions
- deep inheritance hierarchies

## Target user experience

### No saved session

```text
CONTEXT ENGINE LOGIN

Backend: http://127.0.0.1:8000

Email:    [                              ]
Password: [                              ]

Actions:
  Tab Next Field
  Enter Submit
  Q Quit
```

### Authenticated main menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8000
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

Use ↑/↓ to move, Enter to select, B to go back, Q to quit.
```

### Documents screen

```text
DOCUMENTS

+---------+------------+--------+
| ID      | Filename   | Status |
+---------+------------+--------+
| doc_123 | manual.pdf | ready  |
+---------+------------+--------+

Actions:
  ↑/↓ Select document
  Enter Open selected document
  R Retrieve from selected document
  B Back
  Q Quit
```

## Most important implementation rule

Do not implement the TUI as repeated `print()` calls that append output.

The TUI must run as a screen loop:

```python
while not state.should_quit:
    console.clear()
    active_screen = navigation.current()
    console.print(active_screen.render(state))
    key = input_reader.read_key()
    command = active_screen.handle_key(key, state)
    navigation.apply(command)
```

## Proposed package structure

```text
cli/
  commands/
    ui.py

  tui/
    app.py
    keys.py
    navigation.py
    screen.py
    state.py
    styles.py
    widgets.py
    input.py
    screens/
      login.py
      login_failed.py
      main_menu.py
      documents.py
      document_detail.py
      retrieval.py
      lightrag.py
      admin_documents.py
      jobs.py
      observability.py
      backend_gaps.py
      logged_out.py

  screens/
    models.py
    documents.py
    retrieval.py
    lightrag.py
    admin_documents.py
    jobs.py
    observability.py
```

## Implementation phases

1. TUI app loop and navigation stack
2. Login startup and session lifecycle
3. Main menu arrow navigation
4. Screen replacement and clear/redraw behavior
5. Documents screen wired to backend
6. Nested document detail/back navigation
7. Backend gap screen
8. Additional screens
9. Final refactor and documentation
