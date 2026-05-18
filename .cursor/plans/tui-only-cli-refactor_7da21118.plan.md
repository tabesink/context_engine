---
name: tui-only-cli-refactor
overview: Refactor the CLI to make the interactive TUI the only user-facing entrypoint, remove direct ragcli command-mode usage, and preserve backend capabilities through a thin service layer with test-first delivery.
todos:
  - id: phase-a-launcher-entrypoints
    content: Implement launcher and TUI-only script entrypoints; remove ragcli script and add entrypoint smoke tests.
    status: completed
  - id: phase-b-service-extraction
    content: Extract retained API calls into cli/services modules and wire TUI flows/screens to services.
    status: completed
  - id: phase-c-tui-parity
    content: Close TUI parity gaps for retained surfaces with confirmation/error UX and backend-driven auth behavior.
    status: completed
  - id: phase-d-remove-command-tree
    content: Retire direct Typer command tree and delete/update tests that depend on ragcli subcommands.
    status: completed
  - id: phase-e-docs-and-verification
    content: Update README/docs to TUI-only workflow and run focused launcher/service/TUI regression tests.
    status: completed
isProject: false
---

# TUI-Only CLI Refactor (Hard `ragcli` Removal)

## Scope and Intent
Implement the full plan in [d:\Projects\context_engine\docs\cli_docs\07_tui_only\tui_only.md](d:\Projects\context_engine\docs\cli_docs\07_tui_only\tui_only.md) with hard removal of `ragcli` command-mode entrypoints. Use TDD from [d:\Projects\context_engine\.cursor\skills\engineering\tdd\SKILL.md](d:\Projects\context_engine\.cursor\skills\engineering\tdd\SKILL.md): one behavior per red-green cycle, then refactor.

## Current Baseline (Validated)
- CLI entrypoint currently points to `ragcli`: [d:\Projects\context_engine\pyproject.toml](d:\Projects\context_engine\pyproject.toml)
- Large Typer command tree and mixed command+TUI model: [d:\Projects\context_engine\cli\main.py](d:\Projects\context_engine\cli\main.py)
- Existing interactive TUI runtime already present: [d:\Projects\context_engine\cli\tui\app.py](d:\Projects\context_engine\cli\tui\app.py)
- Existing high-value TUI integration tests to extend: [d:\Projects\context_engine\tests\test_cli_tui.py](d:\Projects\context_engine\tests\test_cli_tui.py)

## Delivery Strategy (TDD Vertical Slices)
1. Introduce launcher-first architecture and new script entrypoints.
2. Add/expand service layer behind TUI flows, keeping screens thin.
3. Close feature parity gaps in TUI surfaces that are retained.
4. Remove `ragcli` script and direct command-mode tree.
5. Update docs + tests to enforce TUI-only workflow.

## Implementation Phases

### Phase A — Launcher and Entrypoints
- Add `cli/launcher.py` as a minimal composition root:
  - load config/base URL
  - initialize credentials
  - provide API client factory
  - call `run_tui`
  - clean Ctrl+C exit
- Update [d:\Projects\context_engine\pyproject.toml](d:\Projects\context_engine\pyproject.toml):
  - add `context-engine = "cli.launcher:main"`
  - add `context-tui = "cli.launcher:main"`
  - remove `ragcli` script
- Add smoke tests for launcher/entrypoints in `tests/`.

### Phase B — Service Layer Extraction
- Create `cli/services/` modules for retained surfaces (`auth`, `documents`, `retrieval`, `admin_documents`, `jobs`, `lightrag`, `observability`, `health`).
- Move route calls out of TUI screen/flow orchestration into services.
- Keep screen code focused on navigation/input/rendering only.
- Centralize route paths in service methods (or route constants if needed).

### Phase C — TUI Surface Parity
- Validate and complete coverage for retained capabilities:
  - session/login/logout
  - documents and details/page/structure
  - retrieval/answer/compare
  - admin documents
  - jobs
  - LightRAG labels/graph
  - observability logs
  - health/readiness
- Preserve backend-authoritative permissions (no local role bypasses).
- Ensure destructive actions include explicit confirmations.
- Ensure user-facing friendly errors (no tracebacks).

### Phase D — Remove Direct Command Tree
- Retire `cli/main.py` Typer command-mode interface (delete or reduce to non-user-facing internals only, with imports cleaned).
- Remove/deprecate code paths and tests that depend on direct `ragcli ...` subcommands.
- Keep only TUI launch commands as public CLI.

### Phase E — Docs and Final Verification
- Update README and CLI docs to show only TUI workflow (`context-engine` / `context-tui`).
- Remove command-mode examples and stale references.
- Add a preservation matrix in PR description mapping old capability → API route → TUI path → status.
- Run focused tests for launcher + services + TUI behavior and fix regressions.

## Test-First Plan (Behavior Order)
1. `context-engine` and `context-tui` launch TUI.
2. `ragcli` is no longer installed/exposed.
3. Login/session flow works end-to-end.
4. Each retained surface works through services (method/path/auth/error behavior).
5. Admin-only behavior enforced by backend responses and rendered clearly.
6. Destructive actions require confirmation.
7. Error states render friendly guidance, not raw exceptions.

## Key Files to Change
- [d:\Projects\context_engine\pyproject.toml](d:\Projects\context_engine\pyproject.toml)
- [d:\Projects\context_engine\cli\launcher.py](d:\Projects\context_engine\cli\launcher.py)
- [d:\Projects\context_engine\cli\main.py](d:\Projects\context_engine\cli\main.py)
- [d:\Projects\context_engine\cli\services\__init__.py](d:\Projects\context_engine\cli\services\__init__.py) and `cli/services/*.py`
- [d:\Projects\context_engine\cli\tui\app.py](d:\Projects\context_engine\cli\tui\app.py) and related `cli/tui/screens/*`
- [d:\Projects\context_engine\tests\test_cli_tui.py](d:\Projects\context_engine\tests\test_cli_tui.py) plus new `tests/test_cli_launcher*.py` and `tests/test_cli_services*.py`
- README and related docs under `docs/cli_docs/`

## Risk Controls
- Deliver in small, reviewable commits/PR slices (launcher, services, parity, removal, docs).
- Preserve backend contract; avoid API behavior drift.
- Keep refactors bounded by passing tests after each vertical slice.
- Prefer explicit naming and small modules for junior-dev readability.