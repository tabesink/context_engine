# Phase 5 — Job Queue and Event Log UI

## Goal

Expose admin job queue status and recent lifecycle events in a compact operational surface.

## Scope

Allowed:

- Admin Jobs route.
- Job queue table.
- Recent lifecycle/domain/document event tail.
- Retry/cancel actions only if backend already supports them.
- Filtering by status/domain/type.

Not allowed:

- Building a full observability platform.
- Adding Langfuse or external observability.
- Adding new job runner architecture.
- Exposing internal stack traces to regular users.

## UI pattern

Use Dashboard Job Queue + Timeline/Activity Feed patterns.

## Components

Suggested:

```txt
client/src/components/settings/jobs/JobQueueOverview.tsx
client/src/components/settings/jobs/JobQueueTable.tsx
client/src/components/settings/jobs/JobStatusChip.tsx
client/src/components/settings/jobs/JobEventTimeline.tsx
client/src/components/settings/jobs/JobActionMenu.tsx
```

Reuse existing status primitives.

## Backend/API wiring

Use existing job APIs if present. If missing, add only minimal admin read route:

```txt
GET /admin/jobs?status=&domain_id=&limit=&cursor=
```

Avoid duplicating existing `/jobs` route. Extend it only if compatible.

## Event model

Prefer existing audit/job/lifecycle records if present. If no event model exists, derive an event tail from recent jobs/domain lifecycle updates for now.

Minimum event display:

- time
- actor if available
- domain/document if available
- event type
- status
- message


## shadcn references for this phase

- Dashboard Job Queue: https://www.shadcn.io/blocks/dashboard-job-queue
- Timeline block category: https://www.shadcn.io/blocks/timeline
- Tables block category: https://www.shadcn.io/blocks/tables
- Table primitive: https://ui.shadcn.com/docs/components/table
- Badge primitive: https://ui.shadcn.com/docs/components/badge
- Scroll Area primitive: https://ui.shadcn.com/docs/components/scroll-area

Also open `reference/SHADCN_BLOCK_LINKS.md` before implementation.

## Tests

Frontend:

- renders queued/running/failed/completed jobs
- filters by status
- action menu hidden when unsupported
- no stack traces in regular UI

Backend:

- admin auth required
- pagination works
- filtering works

## Validation

```bash
python -m pytest -q
cd client
npm run lint
npm run build
```

## Human inspection gate

Inspect:

- Is this operationally useful without being bloated?
- Are job statuses consistent with document/domain status chips?
- Is it clearly admin-only?
