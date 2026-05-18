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
