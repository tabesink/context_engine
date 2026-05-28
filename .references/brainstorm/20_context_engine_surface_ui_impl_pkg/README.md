# Context Engine Surface UI Implementation Package

Purpose: guide a coding agent and junior developer through a phase-by-phase UI and lean backend API integration for Context Engine surfaces.

This package is intentionally self-contained. Each phase can be handed to a coding agent independently, completed, reviewed, and then merged before starting the next phase.

## Included documents

- `00_REFINED_CODING_AGENT_PROMPT.md` — single master prompt for the coding agent.
- `01_MASTER_IMPLEMENTATION_PLAN.md` — overview of all phases, dependencies, inspection gates, and acceptance criteria.
- `reference/API_CONTRACTS_AND_WIRING.md` — normalized backend API contracts and wiring guidance.
- `reference/SHADCN_BLOCK_MAPPING.md
- `reference/SHADCN_BLOCK_LINKS.md` — direct shadcn.io block links, category links, shadcn/ui primitive docs, and Cursor MCP setup guidance` — shadcn block patterns mapped to Context Engine surfaces.
- `reference/STATE_AND_POLLING_STRATEGY.md` — frontend state, polling, and concurrent-user strategy.
- `phases/PHASE_0_UI_FOUNDATION_AUDIT.md`
- `phases/PHASE_1_SETTINGS_SHELL_PREP.md`
- `phases/PHASE_2_BACKEND_STATUS_API_WIRING.md`
- `phases/PHASE_3_LIGHTRAG_DOMAIN_LIFECYCLE_UI.md`
- `phases/PHASE_4_DOCUMENT_PROCESSING_STATUS_UI.md`
- `phases/PHASE_5_JOB_QUEUE_AND_EVENT_LOG_UI.md`
- `phases/PHASE_6_USER_SAFE_WORKSPACE_STATUS_UI.md`
- `phases/PHASE_7_FINAL_HARDENING_AND_CLEANUP.md`
- `checklists/PHASE_INSPECTION_CHECKLISTS.md`
- `checklists/DEFINITION_OF_DONE.md`

## Usage

1. Give the coding agent `00_REFINED_CODING_AGENT_PROMPT.md` plus the current phase file.
2. The agent must complete only that phase.
3. Run the phase validation commands.
4. Inspect using `checklists/PHASE_INSPECTION_CHECKLISTS.md`.
5. Merge only after the inspection gate passes.
6. Start the next phase.

## Core guardrails

- Context Engine remains the only frontend-facing API/auth boundary.
- The frontend must not call LightRAG directly.
- Avoid broad rewrites and new dependencies.
- Build UI surfaces with stable Context Engine API contracts, not raw LightRAG metadata.
- Use shadcn patterns as structure, but adapt to Context Engine design: flat grayscale, no shadows, compact cards, restrained borders, pill-shaped interactive elements.
- Prefer small, reviewable patches.


## Direct shadcn references

Open `reference/SHADCN_BLOCK_LINKS.md` before each UI phase. It contains direct block URLs, category URLs, primitive component docs, and MCP setup notes so the coding agent does not need to infer or reverse-search component references.
