---
name: Fix imports add comments
overview: Normalize import paths to `agent.*` and add targeted docstrings/inline comments in `agent` and `cli` for junior readability without overcommenting.
todos:
  - id: normalize-imports-cli
    content: Replace `mybot.*` imports with `agent.*` in CLI files and verify entrypoint import resolution.
    status: completed
  - id: normalize-imports-tools
    content: Replace `mybot.*` imports with `agent.*` in `agent/tools` modules and fix TYPE_CHECKING imports consistently.
    status: completed
  - id: fix-registry-wiring
    content: Align core agent registry import to the implemented command registry module.
    status: completed
  - id: add-docs-comments
    content: Add balanced function docstrings and selective inline comments in chosen `agent` and `cli` files.
    status: completed
  - id: run-lint-smoke
    content: Run lint/smoke checks for touched files and resolve introduced issues.
    status: completed
isProject: false
---

# Fix Imports And Comments Plan

## Scope
- Fix broken/inconsistent imports in `agent` and `cli` by standardizing on `agent.*`.
- Add balanced function documentation: concise docstrings for purpose + selective inline comments only where flow is non-obvious.
- Keep behavior unchanged except where import wiring is currently broken.

## Planned Changes
- Update CLI import namespace from `mybot.*` to `agent.*` in:
  - `[d:/Projects/clawagent/cli/main.py](d:/Projects/clawagent/cli/main.py)`
  - `[d:/Projects/clawagent/cli/chat.py](d:/Projects/clawagent/cli/chat.py)`
  - `[d:/Projects/clawagent/cli/__init__.py](d:/Projects/clawagent/cli/__init__.py)`
- Update tools import namespace from `mybot.*` to `agent.*` in:
  - `[d:/Projects/clawagent/agent/tools/__init__.py](d:/Projects/clawagent/agent/tools/__init__.py)`
  - `[d:/Projects/clawagent/agent/tools/base.py](d:/Projects/clawagent/agent/tools/base.py)`
  - `[d:/Projects/clawagent/agent/tools/registry.py](d:/Projects/clawagent/agent/tools/registry.py)`
  - `[d:/Projects/clawagent/agent/tools/builtin_tools.py](d:/Projects/clawagent/agent/tools/builtin_tools.py)`
  - `[d:/Projects/clawagent/agent/tools/websearch_tool.py](d:/Projects/clawagent/agent/tools/websearch_tool.py)`
  - `[d:/Projects/clawagent/agent/tools/webread_tool.py](d:/Projects/clawagent/agent/tools/webread_tool.py)`
  - `[d:/Projects/clawagent/agent/tools/skill_tool.py](d:/Projects/clawagent/agent/tools/skill_tool.py)`
- Fix likely command-registry wiring mismatch so runtime uses real registry implementation:
  - `[d:/Projects/clawagent/agent/core/agent.py](d:/Projects/clawagent/agent/core/agent.py)` import target aligned to implemented registry.
- Add function-level docs/comments in high-value files:
  - `[d:/Projects/clawagent/cli/chat.py](d:/Projects/clawagent/cli/chat.py)` for `ChatLoop.__init__`, `ChatLoop.run`, and slash-command dispatch path.
  - `[d:/Projects/clawagent/cli/main.py](d:/Projects/clawagent/cli/main.py)` for callback/`ctx.obj` contract.
  - `[d:/Projects/clawagent/agent/utils/def_loader.py](d:/Projects/clawagent/agent/utils/def_loader.py)` for parser helper intent and edge cases.
  - `[d:/Projects/clawagent/agent/commands/handlers.py](d:/Projects/clawagent/agent/commands/handlers.py)` for command handler responsibilities and non-obvious flow.
  - Optional module-level note to disambiguate dual registry modules in:
    - `[d:/Projects/clawagent/agent/core/commands/registry.py](d:/Projects/clawagent/agent/core/commands/registry.py)`
    - `[d:/Projects/clawagent/agent/commands/registry.py](d:/Projects/clawagent/agent/commands/registry.py)`

## Validation
- Run lints on touched files and fix any introduced warnings/errors.
- Smoke-check imports by running CLI entrypoint help and basic module import paths.
- Ensure comments stay concise (no line-by-line narration) and focus on purpose/tricky logic.

## Notes
- Comments will be "balanced" per your choice: concise docstrings + selective inline explanations for tricky branches/event-loop behavior.
- If encountered during edits, any unrelated behavioral bugs will be called out separately, but not expanded unless you request scope increase.