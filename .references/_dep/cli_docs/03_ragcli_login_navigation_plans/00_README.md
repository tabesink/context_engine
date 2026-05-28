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
