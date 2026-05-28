# Phase 0 — UI Foundation Audit and Broad-Change Preparation

## Goal

Prepare the frontend for broad UI changes without building the new status surfaces yet.

This phase is primarily an audit and small-prep phase. The output should be a clear map of current frontend/backend surfaces and a minimal set of safe utilities/components if gaps are obvious.

## Scope

Allowed:

- Inspect current settings/admin/chat/workspace layout.
- Inspect current API client locations.
- Inspect current state stores.
- Inspect current UI component conventions.
- Add tiny shared UI primitives if clearly useful:
  - `StatusChip`
  - `PanelState`
  - `SectionCard`
  - `SurfaceHeader`
- Add comments/TODO docs where future phases will attach.

Not allowed:

- Building full domain lifecycle UI.
- Building document status UI.
- Adding backend routes.
- Refactoring chat retrieval.
- Changing public API contracts.

## Repo inspection commands

```bash
rg -n "Settings|settings|Dialog|Sheet|Account|Provider|LightRAG|Domain" client/src
rg -n "apiRequest|fetch\(|/admin/lightrag|/lightrag/domains|/documents|/jobs" client/src
rg -n "create\(|zustand|use.*Store|Store" client/src/stores client/src
rg -n "SidePanel|WorkspaceTree|SourceNavigator|ContextStream|AssetCards" client/src/components/chat
rg -n "DESIGN.md|design" .
```

## Deliverables

1. `docs/ui-surface-map.md` or equivalent report.
2. Current frontend route/component map.
3. Current API client map.
4. Current state store map.
5. List of proposed reusable primitives.
6. Optional tiny primitives if already consistent with current design.

## Backend/API work

None, except documenting current backend route surfaces.

Inspect:

```bash
rg -n "include_router|APIRouter|/admin/lightrag|/documents|/jobs|processing-status|ingestion-status" app
```

## Frontend work

Suggested small additions only if helpful:

```txt
client/src/components/surfaces/SectionCard.tsx
client/src/components/surfaces/StatusChip.tsx
client/src/components/surfaces/PanelState.tsx
client/src/components/surfaces/SurfaceHeader.tsx
```

If similar components already exist, reuse them and do not duplicate.

## Validation

```bash
cd client
npm run lint
npm run build
```

Backend tests optional in this phase unless files were changed:

```bash
python -m pytest -q
```

## Human inspection gate

The human should inspect:

- Is the proposed UI shell map clear?
- Are there duplicate API client patterns?
- Are proposed primitives minimal?
- Did the agent avoid implementing future phases?
