# context-engine TUI Login + Navigation TDD Implementation Plans



---

# File: 00_README.md

# context-engine TUI Login + Navigation TDD Plan Bundle

This bundle updates the previous `context-engine` plan to include:

- In-TUI login and logout
- Existing-session startup behavior
- Expired-session handling
- Arrow-key navigation
- Enter-to-select behavior
- Screen stack navigation
- Back navigation between screens
- Clear/redraw screen replacement
- Mostly black-and-white visual style
- ASCII tables only
- Backend-gap screens for unsupported planned capabilities
- Vertical TDD slices using red-green-refactor

## Intended use

Give these files to the coding agent in order:

1. `01_EXECUTIVE_IMPLEMENTATION_PLAN.md`
2. `02_TUI_NAVIGATION_AND_SCREEN_STACK_PLAN.md`
3. `03_TUI_LOGIN_LOGOUT_SESSION_PLAN.md`
4. `04_TUI_SCREEN_BEHAVIOR_PLAN.md`
5. `05_TDD_VERTICAL_SLICES.md`
6. `06_TESTING_FIXTURES_AND_MOCKING_PLAN.md`
7. `07_CODING_AGENT_PROMPT.md`

## Non-negotiable constraints

- `context-engine` must not be a scrolling log of `print()` output.
- Every screen transition must clear/redraw the active screen.
- The TUI must reuse the existing CLI auth/session/API boundaries.
- The TUI must not call LightRAG directly.
- The TUI must not infer admin status locally.
- Unsupported backend features must show backend-gap states.
- JSON output for existing command mode must remain unchanged.
- Tests should verify behavior through public interfaces, not private implementation details.



---

# File: 01_EXECUTIVE_IMPLEMENTATION_PLAN.md

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



---

# File: 02_TUI_NAVIGATION_AND_SCREEN_STACK_PLAN.md

# TUI Navigation and Screen Stack Plan

## Goal

Users must be able to navigate the TUI with arrows, select options with Enter, move between screens, and return with Back. The terminal must not accumulate previous screen output.

## User controls

| Key | Behavior |
| --- | --- |
| Up arrow | Move selection up |
| Down arrow | Move selection down |
| Enter | Select highlighted option |
| B | Go back one screen |
| Esc | Optional: go back one screen |
| Q | Quit from any screen |
| Ctrl+C | Exit cleanly |

## Required behavior

- Starting `context-engine` shows login or main menu depending on session state.
- Arrow keys move the selected item.
- Enter opens the selected screen/action.
- The selected screen replaces the previous screen.
- Back returns to the previous screen.
- Quit exits from any screen.
- Nested screens use a stack.
- Loading, error, and backend-gap states replace the current screen; they do not append output.

## Navigation stack

Create a very small navigation stack.

```python
from dataclasses import dataclass, field

@dataclass
class NavigationStack:
    screens: list["TuiScreen"] = field(default_factory=list)

    def push(self, screen: "TuiScreen") -> None:
        self.screens.append(screen)

    def pop(self) -> None:
        if len(self.screens) > 1:
            self.screens.pop()

    def replace(self, screen: "TuiScreen") -> None:
        if self.screens:
            self.screens[-1] = screen
        else:
            self.screens.append(screen)

    def reset(self, screen: "TuiScreen") -> None:
        self.screens = [screen]

    def current(self) -> "TuiScreen":
        return self.screens[-1]
```

## Screen command model

Keep this simple.

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ScreenCommandType(str, Enum):
    NONE = "none"
    PUSH = "push"
    POP = "pop"
    REPLACE = "replace"
    RESET = "reset"
    QUIT = "quit"
    REFRESH = "refresh"

@dataclass
class ScreenCommand:
    type: ScreenCommandType
    screen: Optional["TuiScreen"] = None
```

## TUI screen protocol

```python
from typing import Protocol, Any

class TuiScreen(Protocol):
    title: str

    def render(self, state: "TuiState") -> Any:
        ...

    def handle_key(self, key: str, state: "TuiState") -> ScreenCommand:
        ...
```

## TUI state

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TuiState:
    api_base_url: str
    user_email: Optional[str] = None
    should_quit: bool = False
    last_error: Optional[str] = None
```

## Selection helper

Keep selection movement testable and boring.

```python
def move_selection_up(index: int, item_count: int) -> int:
    if item_count <= 0:
        return 0
    return (index - 1) % item_count

def move_selection_down(index: int, item_count: int) -> int:
    if item_count <= 0:
        return 0
    return (index + 1) % item_count
```

## Screen replacement rule

The TUI loop must call `console.clear()` before every render.

Do not render screens using normal `print()`.

Do not let screen content accumulate in the terminal.

## Main menu screen

Main menu options:

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

Behavior:

- Up/down changes highlighted row.
- Enter on an option pushes or replaces with the selected screen.
- Enter on Logout clears session and resets to login/logged-out screen.
- Enter on Quit exits.
- Q exits.

## Back behavior

- From any child screen, `B` pops back one screen.
- From root main menu, `B` does nothing or shows a quit confirmation.
- From login screen, `B` does nothing.
- From logged-out screen, `B` returns to login or does nothing.

## Acceptance criteria

- User can navigate main menu options with arrow keys.
- User can open selected screen with Enter.
- User can go back with B.
- Terminal content is replaced, not appended.
- Quit works from every screen.
- Screen stack behavior is covered by behavior tests.



---

# File: 03_TUI_LOGIN_LOGOUT_SESSION_PLAN.md

# TUI Login, Logout, and Session Lifecycle Plan

## Goal

The user must be able to complete the full session lifecycle inside `context-engine`:

```text
No session -> login -> main menu -> logout -> login
```

The TUI must reuse the existing CLI auth/session logic.

## Existing command behavior to reuse

Normal CLI command mode already supports:

```bash
context-engine login --email admin@example.com
context-engine logout
context-engine auth me
```

The TUI must reuse the same backend routes and credential storage:

| Action | Backend/local behavior |
| --- | --- |
| Login | `POST /auth/login` |
| Auth check | `GET /auth/me` |
| Logout | local credential clear |

## Startup flow

```text
context-engine
   ↓
Load saved credentials
   ↓
If no credentials:
   show LoginScreen
   ↓
If credentials exist:
   call /auth/me
   ↓
If valid:
   show MainMenuScreen
   ↓
If invalid/expired:
   clear saved credentials
   show LoginScreen with expired-session message
```

## Login screen

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

### Required behavior

- User can type email.
- User can move to password with Tab.
- User can type password.
- Password is masked or hidden.
- Enter submits login.
- Q quits.
- Access token is never printed.
- Password is never printed.
- On success, credentials are stored using existing `CredentialStore`.
- On success, screen clears and main menu is shown.
- On failure, login failed screen is shown.

## Login failed screen

```text
LOGIN FAILED

auth_failed: Invalid email or password.

> Retry
  Quit
```

Behavior:

- Enter on Retry returns to login screen.
- Enter on Quit exits.
- Password is never shown.
- Backend error message may be preserved if safe.

## Existing session valid

When saved credentials exist, call `/auth/me`.

If successful:

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
```

## Existing session expired

If `/auth/me` returns auth failure:

1. Clear saved session.
2. Show login screen with a short message:

```text
CONTEXT ENGINE LOGIN

Previous session expired. Please log in again.

Backend: http://127.0.0.1:8000

Email:    [                              ]
Password: [                              ]
```

## Logout behavior

Main menu includes:

```text
Logout
```

When selected:

1. Clear stored credentials using existing logout/session clear logic.
2. Reset navigation stack.
3. Clear/redraw to logged-out screen or login screen.

Recommended logged-out screen:

```text
LOGGED OUT

Your local CLI session has been cleared.

> Login again
  Quit
```

## TUI auth architecture

Suggested files:

```text
cli/tui/screens/login.py
cli/tui/screens/login_failed.py
cli/tui/screens/logged_out.py
cli/tui/session_flow.py
```

`session_flow.py` can provide small orchestration helpers:

```python
def choose_start_screen(credentials, api_client, credential_store) -> TuiScreen:
    ...
```

Keep it simple. Do not create a TUI-only auth subsystem.

## Security rules

- Do not store passwords.
- Do not print passwords.
- Do not print access tokens.
- Do not echo request headers.
- Do not infer admin role locally.
- Use backend responses for authorization failures.
- Preserve existing command-mode JSON output unchanged.

## Acceptance criteria

- No saved session opens login screen.
- Valid saved session opens main menu.
- Expired saved session clears credentials and opens login screen.
- Successful login stores session and opens main menu.
- Failed login shows retry screen.
- Logout clears credentials and returns to login/logged-out screen.
- Token and password never appear in captured output.



---

# File: 04_TUI_SCREEN_BEHAVIOR_PLAN.md

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



---

# File: 05_TDD_VERTICAL_SLICES.md

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
context-engine
```

starts the TUI app entrypoint.

## Test

```text
`tests/test_cli_launcher.py` and `tests/test_cli_tui.py` (launcher + TUI smoke coverage)
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

Given no stored credentials, `context-engine` opens the login screen.

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

- `context-engine documents list --output json` still returns stable JSON shape
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



---

# File: 06_TESTING_FIXTURES_AND_MOCKING_PLAN.md

# Testing Fixtures and Mocking Plan

## Testing goal

Test `context-engine` through observable user behavior.

Prefer tests that simulate:

- starting the command
- sending keyboard input
- receiving backend responses
- observing rendered terminal output
- checking stored session effects

Avoid tests that assert private methods or internal call order.

## What to mock

Mock system boundaries only.

| Boundary | Mock/stub? | Reason |
| --- | --- | --- |
| Backend HTTP | Yes | External system |
| Credential store | Yes for focused tests | OS keyring/local file side effects |
| Keyboard input | Yes | User input stream |
| Terminal output capture | Yes | Test rendered behavior |
| File system | Sometimes | Upload path tests |
| Internal screens/renderers | No | Code you control |
| Navigation stack | No | Internal behavior should be tested via visible screen changes |
| Screen builders | No | Internal behavior |

## Suggested test helper structure

```text
tests/
  tui/
    conftest.py
    test_tui_startup.py
    test_tui_login.py
    test_tui_navigation.py
    test_tui_documents.py
    test_tui_backend_gaps.py
    test_tui_security.py
    test_tui_command_json_regression.py
```

## Test harness idea

Create a helper that runs the TUI with scripted keys.

```python
def run_tui_with_keys(keys: list[str], *, backend, credentials) -> TuiRunResult:
    ...
```

Return:

```python
@dataclass
class TuiRunResult:
    output: str
    exit_code: int
    backend_calls: list[BackendCall]
    stored_credentials: Optional[StoredCredentials]
```

Keep this helper at the test boundary. Do not expose it as production API.

## Key input representation

Use constants:

```python
KEY_UP = "up"
KEY_DOWN = "down"
KEY_ENTER = "enter"
KEY_TAB = "tab"
KEY_BACK = "b"
KEY_QUIT = "q"
```

Test readability matters.

Example:

```python
result = run_tui_with_keys([
    KEY_DOWN,
    KEY_ENTER,
    KEY_QUIT,
])
```

## Capturing screen replacement

Screen replacement can be tested by final buffer snapshot rather than terminal history.

Recommended design:

- Production TUI clears real console.
- Test TUI uses a fake console with `current_frame`.
- Each clear resets `current_frame`.
- Each render writes to `current_frame`.
- At the end, assert final frame.

Example expected behavior:

```python
assert "DOCUMENTS" in result.final_frame
assert "CONTEXT ENGINE\n\nBackend" not in result.final_frame
```

Avoid relying only on cumulative stdout because real terminal clearing sequences can be noisy.

## Security tests

Add tests for:

```text
test_tui_login_never_prints_access_token
test_tui_login_never_prints_password
test_failed_login_never_prints_password
test_error_screen_does_not_echo_headers
```

## JSON regression tests

The TUI must not change command mode.

Add regression tests for:

```text
context-engine documents list --output json
context-engine documents retrieve --query "x" --output json
context-engine admin documents list --output json
unsupported planned command --output json
```

## Backend error tests

Test:

- auth required
- expired token
- 403 admin error
- LightRAG disabled
- connection failure
- unsupported backend gap

## ASCII table tests

Test table output for:

- documents
- jobs
- backend gaps
- labels/popular labels

Expected:

```python
assert "+" in output
assert "|" in output
assert "┌" not in output
assert "│" not in output
```

## Anti-patterns to avoid

Do not write tests like:

```text
test_login_screen_calls_handle_key
test_navigation_push_called_once
test_private_selected_index_changes
test_render_method_called_twice
```

Better:

```text
test_user_can_log_in_and_reaches_main_menu
test_user_can_open_documents_screen_with_enter
test_back_returns_to_previous_screen
test_documents_screen_renders_ascii_table
```

## Refactor checkpoint

After each green slice, ask:

- Is duplication appearing?
- Is the public interface still small?
- Is the TUI screen logic understandable?
- Did we accidentally add business logic to the TUI?
- Did command-mode JSON remain unchanged?



---

# File: 07_CODING_AGENT_PROMPT.md

# Coding Agent Prompt: Implement `context-engine` Login + Arrow-Key TUI with TDD

You are a senior Python CLI/TUI engineer working in an existing `context-engine` codebase.

## Objective

Implement a lightweight interactive TUI launched by:

```bash
context-engine
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
  context-engine chat

Expected behavior:
  not_supported_by_backend
```

## TDD implementation order

Use vertical red-green-refactor slices.

Do not write all tests first.

### Slice 0

`context-engine` command exists and quits cleanly.

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

- `context-engine` launches successfully.
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

