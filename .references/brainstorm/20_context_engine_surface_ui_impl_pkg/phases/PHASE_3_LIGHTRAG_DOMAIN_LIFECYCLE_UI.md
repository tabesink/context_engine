# Phase 3 — Admin LightRAG Domain Lifecycle UI

## Goal

Build the admin-facing LightRAG domain lifecycle surface using the normalized backend APIs from Phase 2.

## User-facing model

Do not show every backend verb as a top-level button.

Preferred public UI actions:

- Start
- Stop
- Repair
- Archive
- Preview Purge
- Purge Permanently

Advanced/dev-only actions, if kept:

- Recreate container
- Regenerate config

These should be hidden behind an advanced/debug disclosure if exposed at all.

## Scope

Allowed:

- Domain registry table.
- Domain overview/status cards.
- Runtime status card.
- Lifecycle workflow card.
- Action buttons wired to existing admin APIs.
- Poll normalized domain status while visible.
- Show stale/error status gracefully.

Not allowed:

- Rewriting backend lifecycle semantics.
- Removing backend routes.
- Direct frontend LightRAG calls.
- Building document table/job queue surfaces in detail.

## Frontend API client

Suggested:

```txt
client/src/api/lightrag-domain-admin.ts
client/src/api/processing-status.ts
```

Only create if missing; reuse existing `lightrag` clients where appropriate.

## UI components

Suggested:

```txt
client/src/components/settings/lightrag-domains/DomainRegistryTable.tsx
client/src/components/settings/lightrag-domains/DomainOverviewCards.tsx
client/src/components/settings/lightrag-domains/DomainRuntimeStatusCard.tsx
client/src/components/settings/lightrag-domains/DomainLifecycleWorkflowCard.tsx
client/src/components/settings/lightrag-domains/DomainDangerZone.tsx
client/src/components/settings/lightrag-domains/DomainEventTail.tsx
```

## Backend wiring

Use existing admin routes for lifecycle operations:

- start/up
- stop/down
- repair
- archive/delete non-permanent
- purge preview
- purge

Use Phase 2 normalized status route for display.

## Lifecycle action mapping

| UI action | Backend operation | Confirmation |
|---|---|---|
| Start | `up` | no destructive confirm |
| Stop | `down` | light confirm if users may be querying |
| Repair | `repair` | explain container/config/probe recovery |
| Archive | archive/delete non-permanent | confirm |
| Preview Purge | purge preview | required before purge |
| Purge Permanently | purge | type-to-confirm |
| Recreate container | `recreate` | advanced only |
| Regenerate config | `regenerate` | advanced/dev only |

## UI style

Use:

- Dashboard overview cards
- CRUD status workflow pattern
- Monitoring container status pattern
- Settings danger zone pattern

Keep flat/compact.


## shadcn references for this phase

- Dashboard Platform Overview: https://www.shadcn.io/blocks/dashboard-platform-overview
- Monitoring Container Status: https://www.shadcn.io/blocks/monitoring-container-status
- CRUD Status Workflow: https://www.shadcn.io/blocks/crud-status-workflow
- Settings Danger Zone: https://www.shadcn.io/blocks/settings-danger-zone
- Settings Deployment Config: https://www.shadcn.io/blocks/settings-deployment-config
- Button primitive: https://ui.shadcn.com/docs/components/button
- Card primitive: https://ui.shadcn.com/docs/components/card
- Badge primitive: https://ui.shadcn.com/docs/components/badge
- Alert Dialog primitive: https://ui.shadcn.com/docs/components/alert-dialog
- Dropdown Menu primitive: https://ui.shadcn.com/docs/components/dropdown-menu

Also open `reference/SHADCN_BLOCK_LINKS.md` before implementation.

## Tests

Frontend:

- admin can see actions
- non-admin cannot see route/actions
- actions call Context Engine admin API, not LightRAG
- status polling starts when screen visible and stops when unmounted
- stale status chip renders

Backend tests should already exist from Phase 2; add route tests only if lifecycle API changes.

## Validation

```bash
cd client
npm run lint
npm run build
```

If backend touched:

```bash
python -m pytest -q
```

## Human inspection gate

Inspect:

- Are lifecycle actions understandable?
- Are redundant verbs hidden or clarified?
- Does repair feel like the primary recovery action?
- Is Danger Zone safe and explicit?
- Does UI avoid technical noise?
