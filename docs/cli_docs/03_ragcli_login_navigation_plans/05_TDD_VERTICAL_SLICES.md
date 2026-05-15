# TDD Vertical Slices for TUI Login + Navigation

## TDD philosophy

Use vertical slices.

Do not write all tests first.

For each slice:

```text
RED: write one behavior test
GREEN: implement minimal code
REFACTOR: clean only while tests are green
```

Tests should verify behavior through public interfaces and user-visible output.

Mock only system boundaries:

- backend HTTP
- credential storage
- keyboard input stream
- terminal output capture
- file system only where needed

Do not mock internal screens, renderers, navigation stack, or screen builders.

---

# Slice 0: TUI command is registered

## Behavior

Running:

```bash
ragcli ui
```

starts the TUI app entrypoint.

## Test

```text
test_ragcli_ui_starts_tui_app
```

Expected:

- command exists
- exits cleanly when input is `Q`
- does not affect existing command-mode JSON behavior

## Minimal implementation

- Add `commands/ui.py`
- Register `ui` command
- Add placeholder app loop that can quit

---

# Slice 1: No session opens login screen

## Behavior

Given no stored credentials, `ragcli ui` opens the login screen.

## Test

```text
test_ui_starts_at_login_when_no_session_exists
```

Expected output contains:

```text
CONTEXT ENGINE LOGIN
Email
Password
```

Expected output does not contain:

```text
Documents
Retrieval
Admin Documents
```

## Minimal implementation

- Add startup session check
- Add `LoginScreen`
- Render login screen

---

# Slice 2: User can quit from login

## Behavior

Pressing `Q` on the login screen exits cleanly.

## Test

```text
test_user_can_quit_from_login_screen
```

Expected:

- exit code success
- no traceback
- no token/password output

---

# Slice 3: User can log in from TUI

## Behavior

User enters email and password; backend returns token; TUI stores session and opens main menu.

## Test

```text
test_user_can_login_from_tui_and_reaches_main_menu
```

Input sequence:

```text
admin@example.com
Tab
password123
Enter
Q
```

Mock:

- backend `POST /auth/login`
- credential store system boundary

Expected:

- `/auth/login` called with email/password
- credential store receives base URL and token
- output contains authenticated main menu
- output does not contain access token
- output does not contain password

## Minimal implementation

- Add login form state
- Add masked password input
- Call existing auth client method
- Store credentials through existing store
- Reset navigation to main menu

---

# Slice 4: Failed login shows retry

## Behavior

Invalid credentials show a failure screen with retry/quit options.

## Test

```text
test_failed_tui_login_shows_retry_without_leaking_password
```

Expected:

- output contains `LOGIN FAILED`
- output contains backend error message or safe error
- password not printed
- token not printed
- retry returns to login screen

---

# Slice 5: Existing valid session opens main menu

## Behavior

Given stored credentials, startup calls `/auth/me` and opens main menu.

## Test

```text
test_existing_valid_session_opens_main_menu
```

Mock:

- credential store returns saved token and base URL
- backend `GET /auth/me` returns user

Expected:

- output contains `Session: admin@example.com`
- output contains main menu options

---

# Slice 6: Expired session returns to login

## Behavior

Given stored credentials but `/auth/me` fails, clear credentials and show login.

## Test

```text
test_expired_session_is_cleared_and_login_screen_is_shown
```

Expected:

- credential store clear called
- output contains login screen
- output contains expired-session message
- main menu not shown

---

# Slice 7: Main menu arrow navigation

## Behavior

Up/down arrows move selected menu option.

## Test

```text
test_user_can_move_selection_with_arrow_keys
```

Expected:

- initial selected option is `Documents`
- Down selects `Retrieval`
- Down selects `LightRAG Graphs`
- Up selects `Retrieval`

Do not assert on private index values. Assert on rendered selected marker.

---

# Slice 8: Enter opens selected screen

## Behavior

Selecting Documents and pressing Enter opens Documents screen.

## Test

```text
test_enter_opens_selected_screen_and_replaces_output
```

Expected:

- active screen becomes `DOCUMENTS`
- previous main menu content is not accumulated in final screen buffer
- output includes document table or empty state

Mock:

- backend `GET /documents`

---

# Slice 9: Back navigation

## Behavior

Pressing B from Documents returns to Main Menu.

## Test

```text
test_back_returns_to_previous_screen
```

Expected:

- Documents screen visible after selecting Documents
- Main Menu visible after pressing B
- no traceback

---

# Slice 10: Nested document detail navigation

## Behavior

Documents -> selected document -> detail -> B returns to Documents.

## Test

```text
test_back_from_document_detail_returns_to_documents_screen
```

Mock:

- `GET /documents`
- `GET /documents/{document_id}`

Expected:

- detail screen shows selected document
- B returns to document list

---

# Slice 11: ASCII table rendering

## Behavior

Documents screen uses ASCII table borders.

## Test

```text
test_documents_screen_uses_ascii_table
```

Expected output contains:

```text
+-
|
```

Expected output does not contain:

```text
┌
│
└
```

---

# Slice 12: Backend gap screen

## Behavior

Backend gaps screen lists planned unsupported capabilities.

## Test

```text
test_backend_gap_screen_lists_planned_commands_without_fake_behavior
```

Expected:

- output contains `backend gap`
- output contains `not_supported_by_backend`
- does not call fake local implementation

---

# Slice 13: Logout returns to login

## Behavior

Authenticated user selects Logout. Credentials are cleared and login/logged-out screen is shown.

## Test

```text
test_logout_clears_session_and_returns_to_login_screen
```

Expected:

- credential store clear called
- output contains `LOGGED OUT` or login screen
- main menu no longer shown after logout

---

# Slice 14: TUI preserves command-mode JSON behavior

## Behavior

Adding TUI must not break existing commands.

## Test

```text
test_documents_list_json_output_is_unchanged_after_tui_addition
```

Expected:

- `ragcli documents list --output json` still returns stable JSON shape
- no TUI formatting leaks into command-mode JSON

---

# Slice 15: LightRAG screen uses backend proxy only

## Behavior

LightRAG screen calls backend graph proxy route and never calls LightRAG directly.

## Test

```text
test_lightrag_tui_screen_uses_backend_graph_proxy
```

Mock:

- backend `GET /graph/label/popular` or `/graphs`

Expected:

- backend proxy route called
- no direct LightRAG service URL required in TUI

---

# Slice 16: Admin screen renders backend 403

## Behavior

Non-admin user opens Admin Documents; backend returns 403; TUI renders error.

## Test

```text
test_admin_screen_renders_backend_403_without_local_admin_check
```

Expected:

- request sent to backend
- error screen shows backend 403 message
- no local role inference required

---

# Slice 17: Refactor pass

After all tests pass:

- extract duplicated key handling
- centralize ASCII table helper
- centralize styles
- keep screen interfaces small
- avoid deep inheritance
- rerun full test suite
