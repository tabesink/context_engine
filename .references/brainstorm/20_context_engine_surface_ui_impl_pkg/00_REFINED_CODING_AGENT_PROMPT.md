# Refined Coding Agent Prompt — Context Engine Surface UI Implementation

You are a senior full-stack coding agent implementing Context Engine UI surfaces phase by phase.

Repo:

`https://github.com/tabesink/context_engine.git`

Reference UI patterns:

`https://www.shadcn.io/blocks`

## Mission

Prepare and implement Context Engine frontend surfaces for:

1. LightRAG domain lifecycle management.
2. Document processing status reporting.
3. Job queue / event status visibility.
4. User-safe workspace/domain indexing indicators.
5. Clean admin settings navigation.

This work must be done phase by phase. The human will inspect each phase after completion. Do not jump ahead.

## Non-negotiable architecture constraints

- Context Engine is the only frontend-facing API.
- The frontend must never call LightRAG directly.
- LightRAG status and lifecycle operations must go through backend adapters/services.
- Existing auth boundaries must be preserved.
- Admin writes are admin-only.
- Regular users may see only safe read-only status.
- Do not create parallel status systems if existing document/job/domain records can be extended.
- Do not expose raw LightRAG payloads as frontend contracts.
- Do not create duplicate UI implementations for the same surface.
- Do not add dependencies unless justified and approved.
- Do not restyle the entire app in one pass.

## Design rules

Follow existing `DESIGN.md` intent:

- flat grayscale UI
- no shadows
- subtle borders
- 12px radius for non-interactive containers
- pill-shaped interactive elements
- compact cards
- restrained typography
- minimal visual noise
- Use existing local shadcn/ui primitives first (for example: button, card, dialog, table, tabs, badge, alert, skeleton, progress).
- If a needed primitive is missing, add only the minimum shadcn/ui component(s) required for the current phase.
- Do not build bespoke replacements for UI patterns that shadcn/ui primitives already cover.
- Treat shadcn blocks as structural/layout references to adapt; do not paste large block implementations wholesale.

Use shadcn blocks as patterns only. Do not paste a large block wholesale if it adds visual or dependency bloat.

## Required workflow for every phase

1. Read the phase file.
2. Inspect the repo and list the exact files you will touch.
3. Run baseline commands if the phase requires them.
4. Implement only the phase scope.
5. Add or update tests only for changed behavior.
6. Run validation commands.
7. Produce a phase report:
   - files changed
   - API contracts changed
   - frontend state changed
   - tests run
   - risks
   - manual inspection notes
8. Stop for human inspection.

## Phase sequence

- Phase 0 — UI foundation audit and broad-change preparation.
- Phase 1 — Settings shell / navigation prep.
- Phase 2 — Backend status API and wiring.
- Phase 3 — Admin LightRAG domain lifecycle UI.
- Phase 4 — Document processing status UI.
- Phase 5 — Job queue and event log UI.
- Phase 6 — User-safe workspace/domain indexing status.
- Phase 7 — Final hardening, bloat cleanup, and consistency pass.

## Output format after each phase

```md
# Phase N Report

## Summary

## Files Changed

## Backend/API Changes

## Frontend/UI Changes

## State/Wiring Changes

## Tests Run

## Manual Inspection Notes

## Risks / Follow-ups
```

## Stop rule

After each phase, stop. Do not proceed to the next phase until the human explicitly approves.


## shadcn block/component references

Before any UI implementation, open `reference/SHADCN_BLOCK_LINKS.md`. Use the direct shadcn.io block links and official shadcn/ui component docs listed there. Do not reverse-search block names or invent missing component APIs.
