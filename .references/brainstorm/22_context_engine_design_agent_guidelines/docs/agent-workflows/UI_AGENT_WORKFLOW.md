# UI Agent Workflow

## Overview

Use four specialized sub-agents for UI work. Each agent produces or consumes explicit files so the work is auditable and junior-developer-friendly.

```txt
User request
  ↓
01 Requirements Analyzer
  ↓ produces specs/<surface>/requirements.md
02 shadcn Component Researcher
  ↓ produces specs/<surface>/component-research.md
03 Implementation Builder
  ↓ produces specs/<surface>/implementation-plan.md and code changes
04 Playwright UX Verifier
  ↓ produces specs/<surface>/verification-report.md and fix list
```

## Phase 1 — Requirements Analyzer

Goal: convert the user request into a concrete UI spec before research or coding.

Inputs:

- User request.
- Existing `design.md` / design guidelines.
- Current route/component files.
- Backend API contracts for the target surface.
- Any screenshots or transcript notes.

Outputs:

- `specs/<surface>/requirements.md`

Required content:

- Current capabilities that must be retained.
- User roles and permissions.
- Data dependencies.
- Required states.
- Acceptance criteria.
- Non-goals.
- Risks.

## Phase 2 — shadcn Component Researcher

Goal: research relevant shadcn components/blocks before implementation.

Inputs:

- `specs/<surface>/requirements.md`
- Existing component inventory.
- Available registries/components from MCP.

Outputs:

- `specs/<surface>/component-research.md`

Required content:

- Candidate blocks/components.
- Installation commands.
- Composition plan.
- Fit/rejection rationale.
- Accessibility notes.
- Responsive behavior.

## Phase 3 — Implementation Builder

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
- Keep feature-level API hooks inside `features/<feature>/`.
- Keep shadcn primitives in `components/ui/`.
- Prefer extraction over duplication after a repeated pattern appears twice.
- Use mock data only as a stepping stone; remove or isolate it before final API wiring.
- Include loading/error/empty states in the first implementation, not as cleanup.

## Phase 4 — Playwright UX Verifier

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

