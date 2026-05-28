# context-engine TDD Implementation Plans

This bundle contains test-driven implementation plans for evolving `context-engine` into an API-first command CLI with:

- clean human “screen-like” renderers
- lightweight shared screen models
- optional black-and-white TUI mode
- ASCII tables
- semantic color used sparingly for API groups
- behavior-first tests through public CLI/TUI interfaces
- explicit `not_supported_by_backend` handling for planned backend gaps

## Source assumptions

These plans assume the uploaded docs are the source of truth:

- `api-contract.md`
- `commands.md`
- `README.md`
- `security-and-output.md`
- `tdd-build-plan.md`
- TDD notes: `SKILL.md`, `tests.md`, `mocking.md`, `interface-design.md`, `deep-modules.md`, `refactoring.md`

## Recommended reading order

1. `01_MASTER_TDD_IMPLEMENTATION_PLAN.md`
2. `02_PHASE_1_HUMAN_SCREEN_RENDERERS.md`
3. `03_PHASE_2_SCREEN_MODELS_AND_API_BOUNDARIES.md`
4. `04_PHASE_3_LIGHTWEIGHT_TUI.md`
5. `05_PHASE_4_GUIDED_FLOWS_AND_FRONTEND_TRACEABILITY.md`
6. `06_TESTING_STRATEGY_AND_FIXTURES.md`
7. `07_CODING_AGENT_IMPLEMENTATION_PROMPT.md`

## Core rule

The CLI and TUI are not separate products.

They are two renderers over the same backend API contract:

```text
CLI command  ─┐
              ├─> API client → screen/result model → renderer
TUI screen   ─┘
```

## Non-negotiables

- Do not call LightRAG directly from the CLI.
- Do not infer admin permission locally.
- Do not print tokens/passwords.
- Do not break `--output json`.
- Do not fake planned backend features.
- Use ASCII tables for human/TUI output.
- Keep code boring, small, and junior-readable.
