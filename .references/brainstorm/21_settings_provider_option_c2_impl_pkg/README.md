# Context Engine — Provider Page Implementation Package
## Target design: Option C2 — Borderless Rows

This package is a handoff bundle for a **junior developer** and a **coding agent** to implement the **Settings → Provider** page using the **Option C2 — Borderless Rows** layout.

## Goal
Implement a flatter, more borderless provider-management page that preserves current capabilities while aligning the UI to the Option C2 mockup:
- show provider list and status
- show selected provider details
- allow secure credential entry and save
- show profile usage counts
- show provider health / connection summary
- allow refresh status
- preserve existing Settings shell and routing

## Included docs
- `01-product-scope.md` — scope, goals, non-goals, required capabilities
- `02-layout-spec.md` — page structure, spacing, visual rules, content hierarchy
- `03-component-architecture.md` — component tree and prop contracts
- `04-state-and-data-flow.md` — client state, query/mutation model, error/loading states
- `05-api-wiring.md` — lean integration guidance and expected backend contracts
- `06-implementation-phases.md` — phased build plan for junior dev / coding agent
- `07-acceptance-checklist.md` — definition of done and QA checklist
- `08-agent-build-prompt.md` — self-contained build prompt for a coding agent
- `assets/option-c2-reference.png` — reference render

## Recommended implementation style
- Keep the implementation **lean**.
- Reuse existing app shell, settings sidebar, auth, and query utilities.
- Avoid introducing a parallel design system.
- Prefer composition over abstraction-heavy patterns.
- Add only the minimal new primitives needed for this page.
