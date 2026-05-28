# UI Agent Workflow

## Overview

Use this workflow for meaningful frontend UI surface changes. Each phase produces or consumes explicit files so the work is auditable and easy for another agent or developer to resume.

```txt
User request
  ↓
01 Requirements Analyzer
  ↓ produces specs/<surface>/requirements.md
02 shadcn Component Researcher
  ↓ produces specs/<surface>/component-research.md
03 Implementation Builder
  ↓ produces specs/<surface>/implementation-plan.md and code changes
04 UX Verifier
  ↓ produces specs/<surface>/verification-report.md and fix list
```

Tiny visual fixes may use the same principles as a lightweight checklist without creating all four files.

## Phase 1 - Requirements Analyzer

Goal: convert the user request into a concrete UI spec before research or coding.

Inputs:

- User request.
- `DESIGN.md` and docs under `docs/design/`.
- Current route/component files.
- Backend/API contracts for the target surface.
- Screenshots or reference notes, if provided.

Output:

- `specs/<surface>/requirements.md`

Required content:

- Current capabilities that must be retained.
- User roles and permissions.
- Data dependencies.
- Required states.
- Acceptance criteria.
- Non-goals.
- Risks and ambiguities.

## Phase 2 - shadcn Component Researcher

Goal: research relevant shadcn components/blocks before implementation.

Inputs:

- `specs/<surface>/requirements.md`
- `client/components.json`
- Current component inventory.
- Available shadcn MCP or registry information.

Output:

- `specs/<surface>/component-research.md`

Required content:

- Candidate blocks/components.
- Installation commands, if any.
- Composition plan.
- Fit/rejection rationale.
- Accessibility notes.
- Responsive behavior.

## Phase 3 - Implementation Builder

Goal: implement a production-ready UI slice using requirements and research as source of truth.

Inputs:

- `specs/<surface>/requirements.md`
- `specs/<surface>/component-research.md`
- Existing frontend code.
- Existing API contracts.

Outputs:

- Code changes.
- `specs/<surface>/implementation-plan.md`

Rules:

- Do not redesign backend contracts unless explicitly requested.
- Keep shadcn primitives in `client/src/components/ui/`.
- Keep shared surface primitives in `client/src/components/surfaces/`.
- Keep surface-owned UI in the current surface folders first, such as `client/src/components/settings/` or `client/src/components/chat/`.
- Prefer extraction over duplication after a repeated pattern appears in at least two real surfaces.
- Use mock data only as a stepping stone; remove it or isolate it before final API wiring.
- Include loading/error/empty states in the first implementation, not as cleanup.

## Phase 4 - UX Verifier

Goal: visually inspect the implemented UI, compare it to requirements, and fix mismatch.

Inputs:

- Running local app.
- Requirements and component research files.
- Changed routes.

Outputs:

- `specs/<surface>/verification-report.md`
- Screenshots when useful.
- A fix list and any applied fixes.

Checks:

- Visual hierarchy.
- Contrast and readability.
- Button states.
- Admin-only visibility.
- Form affordance.
- Responsive behavior.
- Empty/loading/error states.
- No lost functionality.

## Completion Rule

For meaningful UI surface work, do not call the implementation complete until the verification report exists or the final handoff clearly explains why verification could not run.
