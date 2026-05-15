# Coding Agent Prompt: Implement `ragcli ui` Login + Arrow-Key TUI with TDD

You are a senior Python CLI/TUI engineer working in an existing `ragcli` codebase.

## Objective

Implement a lightweight interactive TUI launched by:

```bash
ragcli ui
```

The TUI must support:

- login inside the TUI
- logout inside the TUI
- existing-session startup
- expired-session fallback to login
- arrow-key navigation
- Enter-to-select behavior
- Back navigation between screens
- clear/redraw screen replacement
- mostly black-and-white UI
- ASCII tables only
- backend-gap screens for unsupported planned capabilities

The implementation must be senior-quality but junior-readable.

## Required user experience

### No session

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

### Screen transition rule

When the user selects an option, clear the screen and show only the selected screen.

Do not append new screen output below old screen output.

## Hard constraints

- Reuse existing `CredentialStore`.
- Reuse existing `ApiClient`.
- Reuse existing `/auth/login`, `/auth/me`, and logout behavior.
- Reuse existing query payload builders.
- Do not call LightRAG directly.
- Do not infer admin permissions locally.
- Do not fake backend-gap functionality.
- Do not print access tokens.
- Do not print passwords.
- Do not change command-mode JSON output.
- Do not add complex framework-heavy abstractions.
- Do not mock internal modules in tests.

## Suggested architecture

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
```

## TUI loop

Use a full-screen redraw loop.

```python
while not state.should_quit:
    console.clear()
    screen = navigation.current()
    console.print(screen.render(state))

    key = input_reader.read_key()
    command = screen.handle_key(key, state)
    navigation.apply(command)
```

Do not use ordinary `print()` calls inside screens.

## Navigation

Use a simple stack:

```text
Main Menu
  -> Documents
     -> Document Detail
        -> Page Viewer
```

Rules:

- Enter opens selected screen.
- B goes back.
- Q quits.
- Esc may go back.
- Ctrl+C exits cleanly.
- Logout clears credentials and returns to login/logged-out screen.

## Visual style

Use:

- plain terminal foreground/background
- ASCII tables
- minimal color
- semantic color only for errors, warnings, success, disabled states, or subtle API group accent

Avoid:

- Unicode box drawing
- animations
- emojis
- decorative color
- heavy panels
- scroll-log UI

If using Rich tables:

```python
from rich import box
Table(box=box.ASCII)
```

## Backend gaps

Unsupported planned capabilities must show a disabled/backend-gap screen.

Example:

```text
CHAT

Status: backend gap

This screen is planned, but the backend route does not exist yet.

Equivalent CLI command:
  ragcli chat

Expected behavior:
  not_supported_by_backend
```

## TDD implementation order

Use vertical red-green-refactor slices.

Do not write all tests first.

### Slice 0

`ragcli ui` command exists and quits cleanly.

### Slice 1

No session opens login screen.

### Slice 2

User can quit from login.

### Slice 3

User can log in from TUI and reaches main menu.

### Slice 4

Failed login shows retry without leaking password.

### Slice 5

Existing valid session opens main menu.

### Slice 6

Expired session clears credentials and returns to login.

### Slice 7

Arrow keys move main menu selection.

### Slice 8

Enter opens selected screen and replaces output.

### Slice 9

Back returns to previous screen.

### Slice 10

Nested document detail navigation works.

### Slice 11

Documents screen uses ASCII tables.

### Slice 12

Backend gaps screen lists unsupported capabilities.

### Slice 13

Logout clears session and returns to login/logged-out screen.

### Slice 14

Command-mode JSON remains unchanged.

### Slice 15

LightRAG TUI screens use backend graph proxy only.

### Slice 16

Admin screens render backend 403 without local admin inference.

### Slice 17

Refactor while tests are green.

## Test style

Good tests:

```text
test_user_can_log_in_from_tui_and_reaches_main_menu
test_user_can_move_selection_with_arrow_keys
test_enter_opens_selected_screen_and_replaces_output
test_back_returns_to_previous_screen
test_documents_screen_uses_ascii_table
test_logout_clears_session_and_returns_to_login_screen
```

Bad tests:

```text
test_handle_key_calls_navigation_push
test_private_selected_index_incremented
test_render_called_once
```

## Acceptance criteria

Implementation is done when:

- `ragcli ui` launches successfully.
- No session opens login screen.
- User can log in from TUI.
- User can log out from TUI.
- Existing valid session opens main menu.
- Expired session returns to login.
- Arrow keys navigate options.
- Enter opens selected screen.
- B goes back.
- Q quits.
- Screen transitions clear/redraw.
- Tables are ASCII.
- UI is mostly black and white.
- Unsupported features are shown as backend gaps.
- TUI reuses existing backend API boundaries.
- Command-mode JSON output remains unchanged.
- Tests cover login, navigation, redraw, backend gaps, ASCII tables, and security.
