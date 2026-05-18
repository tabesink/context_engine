# Context Engine + LightRAG Domain Deployment Integration Plan v2

Generated: 2026-05-18

## Purpose

This package is the rewritten implementation plan for integrating Easy Deploy LightRAG-style domain deployment capabilities into `context_engine` while keeping the codebase simple, modular, and low entropy.

The design decisions are locked from project owner answers:

- `context_engine` is the only app operators should use.
- `easy-deploy-lightrag` is source material only; do not copy it wholesale.
- Runtime LightRAG traffic remains HTTP-only through the existing adapter boundary.
- Context Engine must never import LightRAG Python internals.
- Each LightRAG domain is a separate LightRAG container.
- One uploaded document belongs to exactly one LightRAG domain.
- All configurable LightRAG settings are declared in root `.env.example`.
- Generated per-domain env files are outputs only; humans should not edit them.
- The Rich terminal UI exposes LightRAG domain deployment under an admin screen.
- TUI screens call `cli/services/`; Docker/domain logic stays out of screens.
- Domain deployment API routes are admin-only.
- Normal users may see available domains for query selection.
- Context Engine may manage domains with Docker Compose on the same machine.
- Context Engine should support both host-run and Docker-run modes.
- Default domain removal archives data. Permanent delete requires explicit opt-in.
- Domain storage lives under `.data/lightrag/domains/<domain>/`.
- All local/runtime storage should stay under `.data/` where practical.
- The goal is to add LightRAG deployment as a small admin-control feature inside Context Engine, not to merge a second application.

## Files in This Package

| File | Purpose |
|---|---|
| `01_final_architecture_decisions.md` | Final architecture model, control plane vs data plane, what to keep and what to avoid. |
| `02_single_source_env_and_storage.md` | Root `.env.example` as source of truth and `.data/` storage layout. |
| `03_backend_module_api_plan.md` | Proposed backend modules, schemas, services, and admin/user API routes. |
| `04_tui_integration_plan.md` | How to integrate into the current `cli/launcher.py`, `cli/services/`, and `cli/tui/` architecture. |
| `05_domain_lifecycle_and_document_flow.md` | Domain create/up/down/remove flow and one-document-one-domain upload/index model. |
| `06_docker_compose_execution_plan.md` | Docker Compose strategy for host-run and Docker-run Context Engine modes. |
| `07_tdd_and_quality_plan.md` | Test-first implementation slices that avoid live Docker/LightRAG dependencies. |
| `08_coding_agent_prompt.md` | A ready-to-use implementation prompt for a coding agent. |
| `context_engine_lightrag_deploy_v2_combined.md` | One combined Markdown report. |

## Core Summary

The clean design is:

```text
Context Engine
  ├── Runtime LightRAG integration
  │     ├── query/retrieve/answer
  │     ├── upload forwarding
  │     └── graph proxy
  │
  └── LightRAG domain deployment control
        ├── create/list/show domains
        ├── generate domain env/config
        ├── generate compose file
        ├── start/stop/recreate containers
        └── archive/remove domains safely
```

Do not build a second app inside `context_engine`. Build one small admin-control module and keep existing runtime adapters.
