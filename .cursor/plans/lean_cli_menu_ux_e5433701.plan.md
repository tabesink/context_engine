---
name: Lean CLI Menu UX
overview: Add an additive `cli menu` arrow-key selector that loops between Login, Chat, and Agents List, while preserving all existing CLI commands unchanged.
todos:
  - id: add-menu-command
    content: Add additive `menu` command wiring in `src/cli/main.py` without changing existing command behavior.
    status: completed
  - id: build-menu-controller
    content: Create `src/cli/menu.py` with arrow-key selector loop and extensible menu item structure.
    status: completed
  - id: wire-existing-actions
    content: Connect selector actions to existing `login`, `chat`, and `agents list` command flows.
    status: completed
  - id: align-dependencies
    content: Add arrow-selection dependency and keep `requirements.txt` and `pyproject.toml` consistent.
    status: completed
  - id: update-cli-docs
    content: Document `deploy.ps1 cli menu` usage and loop/quit behavior in `scripts/README.md`.
    status: completed
  - id: run-smoke-validation
    content: Smoke test existing commands plus new `menu` path through direct CLI and deploy wrapper.
    status: completed
isProject: false
---

# Lean `cli menu` Selector (Arrow-Key, Additive)

## Agreed Decisions
- Entry point is new command: `cli menu` (no-arg `cli` remains help behavior).
- Use arrow-key selection UX (allowed to add one dependency).
- Menu loops back after each action; user exits only via explicit Quit.
- Scope includes the three actions now (`login`, `chat`, `agents list`) with an extensible structure for future items.
- Existing commands must remain backward-compatible and unchanged in behavior.

## Target Files
- [d:\Projects\clawagent\src\cli\main.py](d:\Projects\clawagent\src\cli\main.py)
- [d:\Projects\clawagent\src\cli\menu.py](d:\Projects\clawagent\src\cli\menu.py) (new)
- [d:\Projects\clawagent\requirements.txt](d:\Projects\clawagent\requirements.txt)
- [d:\Projects\clawagent\pyproject.toml](d:\Projects\clawagent\pyproject.toml)
- [d:\Projects\clawagent\scripts\README.md](d:\Projects\clawagent\scripts\README.md)

## Implementation Plan
- Add a new Typer command in `main.py`: `@app.command("menu")`.
- Introduce `menu.py` with a small, extensible menu controller:
  - defines menu items (`Login`, `Chat`, `Agents List`, `Quit`)
  - presents arrow-key selector and executes selected action
  - always returns to selector after action completion/failure unless Quit
- Wire menu actions to existing command functions (do not alter command signatures/outputs):
  - Login -> existing `login(...)` flow
  - Chat -> existing `chat(...)` / `chat_command(...)` flow
  - Agents List -> existing `agents_list(...)` flow
- Add one dependency for arrow-key selection and ensure dependency declarations are aligned in both dependency files to avoid environment drift.
- Update script docs with a new usage example for `deploy.ps1 cli menu` and short behavior notes.

## Validation Plan
- Command compatibility:
  - `python -m cli.main login ...` still works unchanged
  - `python -m cli.main chat` still works unchanged
  - `python -m cli.main agents list` still works unchanged
- New flow:
  - `python -m cli.main menu` opens selector
  - Up/down + Enter select actions
  - After each action returns, menu is shown again
  - Quit exits cleanly with zero-error exit path
- Deploy wrapper check:
  - `./scripts/deploy.ps1 cli menu` launches the new selector path.

## Non-Goals (for this cut)
- No full-screen TUI framework.
- No change to default no-arg `cli` behavior.
- No behavior changes to existing commands outside adding `menu` entrypoint.