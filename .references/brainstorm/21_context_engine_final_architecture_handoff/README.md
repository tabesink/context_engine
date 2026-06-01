# Context Engine Final Architecture Handoff Package

This package translates the senior architecture recommendations into a phase-by-phase implementation plan for the `v1` branch of Context Engine.

Repository target:

```text
https://github.com/tabesink/context_engine/tree/v1
```

## Goal

Move Context Engine toward a lean, low-entropy architecture where:

```text
Documents own uploaded files and local structure.
Domains own LightRAG runtime/workspace identity.
Operations own all async/global visibility.
processing-status is the only document status API.
Provider config is static/env-driven unless intentionally kept runtime-editable.
Frontend talks to one typed API layer.
```

## Package Contents

```text
context_engine_final_architecture_handoff/
├── README.md
├── IMPLEMENTATION_PLAN.md
├── docs/
│   ├── 01_target_architecture.md
│   ├── 02_phase_by_phase_tasks.md
│   ├── 03_api_contract_migration.md
│   ├── 04_database_model_ownership.md
│   ├── 05_worker_status_operations_plan.md
│   ├── 06_frontend_wiring_plan.md
│   ├── 07_provider_config_plan.md
│   ├── 08_testing_acceptance_criteria.md
│   ├── 09_junior_dev_checklist.md
│   └── 10_coding_agent_prompt.md
```

## How to Use This Package

1. Give `IMPLEMENTATION_PLAN.md` to the coding agent as the main instruction file.
2. Give `docs/09_junior_dev_checklist.md` to the junior developer as the safe execution checklist.
3. Use `docs/10_coding_agent_prompt.md` as the actual prompt for a code-editing agent.
4. Do not implement all phases in one giant pull request.
5. Complete each phase with tests before moving to the next phase.

## Non-Goals

This package does not attempt to redesign the whole application from scratch. It preserves the existing Context Engine shape while removing duplicated concepts, confusing status surfaces, and avoidable runtime configuration complexity.
