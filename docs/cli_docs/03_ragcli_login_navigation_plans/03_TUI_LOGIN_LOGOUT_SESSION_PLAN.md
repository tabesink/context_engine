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
