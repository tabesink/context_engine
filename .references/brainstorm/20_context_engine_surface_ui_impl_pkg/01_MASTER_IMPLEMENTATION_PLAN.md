# Master Implementation Plan — Context Engine Surface UI Rollout

## Objective

Build the Context Engine admin/user UI surfaces in controlled, inspectable phases while keeping backend integration lean and preserving existing architecture.

The broad UI change must be prepared before major feature work. The first phases create navigation, layout, API contracts, and state boundaries. Later phases add domain lifecycle, document status, jobs, and user-safe indicators.

## Target UI surfaces

| Surface | Audience | Purpose | Backend source | shadcn pattern |
|---|---|---|---|---|
| Settings shell | all users, admin routes gated | stable route/navigation framework | existing auth/user/settings APIs | Settings, Sidebar, Dialog |
| LightRAG Domains | admin | domain lifecycle control plane | `/admin/lightrag/domains/*` + new normalized status | Dashboard, CRUD Status Workflow, Monitoring |
| Document processing | admin | upload/ingestion/indexing status | document registry + jobs + LightRAG status adapter | Dashboard PDF Processing, Tables, File Upload |
| Jobs | admin | background job queue and failures | `/jobs` or admin job APIs | Dashboard Job Queue, Tables |
| Domain indexing indicator | regular users | safe read-only processing awareness | user-safe domain status API | Stats, Banner, Status Chip |
| Workspace/source panel badge | regular users | show selected source/document readiness | source context + document status | Badge/Status inline pattern |
| Danger zone | admin only | archive/purge/recover controls | lifecycle/purge APIs | Settings Danger Zone |

## Implementation principles

- Stabilize APIs before UI complexity.
- Add one frontend API client per backend surface.
- Add one polling/store layer for processing status.
- Deduplicate polling by domain.
- Keep chat retrieval state separate from status state.
- Treat LightRAG as backend-only.
- Do not mirror every backend lifecycle endpoint as a top-level button.

## Phase overview

### Phase 0 — UI foundation audit and broad-change prep

No major feature. Audit current shell, routes, components, API clients, state stores, and design tokens. Produce a small compatibility map and add only safe preparation helpers if needed.

### Phase 1 — Settings shell prep

Create or refine a settings/admin shell with left navigation and route slots. No heavy domain status logic yet. Keep existing account/user management intact.

### Phase 2 — Backend status API and wiring

Add normalized backend status contracts and routes. Join existing document/job/domain state with LightRAG status adapter snapshots. Add safe user route and admin detailed routes.

### Phase 3 — Admin LightRAG domain lifecycle UI

Build the admin domain control surface. Reduce lifecycle action noise: Start, Stop, Repair, Archive, Preview Purge, Purge. Hide advanced Recreate/Regenerate unless explicitly enabled.

### Phase 4 — Document processing status UI

Build admin document status table/cards and upload flow status chips using normalized status APIs.

### Phase 5 — Job queue and event log UI

Build job queue surface and lifecycle event history. Keep it compact and admin-only.

### Phase 6 — User-safe workspace/domain status

Add subtle user-facing domain indexing indicator near domain selector/workspace tree. Add source status badge where appropriate. No admin-only detail exposure.

### Phase 7 — Final hardening and cleanup

Remove duplicate UI helpers, consolidate status chips, ensure API clients are consistent, run tests/build, and document remaining technical debt.

## Inspection gates

Each phase must pass:

1. Scope gate — no implementation beyond the current phase.
2. API gate — no direct frontend LightRAG call.
3. Design gate — flat, compact, grayscale UI.
4. Auth gate — admin-only details protected.
5. State gate — no duplicate status/retrieval state.
6. Validation gate — tests/build/lint run or pre-existing failures documented.

## Recommended branch strategy

- `ui/phase-0-foundation-audit`
- `ui/phase-1-settings-shell`
- `api/phase-2-processing-status`
- `ui/phase-3-domain-lifecycle`
- `ui/phase-4-document-status`
- `ui/phase-5-jobs-events`
- `ui/phase-6-user-status`
- `ui/phase-7-hardening-cleanup`

Merge each phase only after human inspection.


## Required shadcn reference file

Before implementing any UI phase, the coding agent must open `reference/SHADCN_BLOCK_LINKS.md` and use the listed block/component links as references. Blocks are inspiration patterns only; implementation must reuse or install local shadcn/ui primitives and adapt them to Context Engine `DESIGN.md`.
