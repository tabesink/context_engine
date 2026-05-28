# Phase 6 — User-Safe Workspace/Domain Status UI

## Goal

Show regular users a subtle, safe indication that a selected domain is indexing or partially unavailable, without exposing admin-only details.

## Scope

Allowed:

- Domain indexing chip near domain selector.
- Workspace tree status banner if documents are still processing.
- Source navigator selected-document status badge.
- Read-only counts: processing, indexed, failed if safe.
- Slow polling using user-safe endpoint.

Not allowed:

- Admin-only operation messages.
- Raw LightRAG history messages.
- Start/stop/repair/archive/purge actions.
- Retrieval filter mutation based on status.
- Blocking chat unless backend explicitly returns domain unavailable.

## UI placement

1. Domain selector/composer area:
   - small chip: `Indexing`, `Ready`, `Partial`, `Status stale`

2. Workspace tree header:
   - muted banner if processing docs exist

3. Source Navigator:
   - selected document status badge, if status known

## Components

Suggested:

```txt
client/src/components/chat/DomainIndexingIndicator.tsx
client/src/components/chat/WorkspaceStatusBanner.tsx
client/src/components/chat/SourceStatusBadge.tsx
```

Reuse status store/hook. Do not put polling logic inside each chip.

## API usage

Use only:

```txt
GET /lightrag/domains/{domain_id}/processing-status
```

This route must return safe data for regular users.

## Polling

- 15–30s while visible.
- Stop if domain idle and no processing/failure count.
- Restart on domain switch.
- Do not poll if no domain selected.


## shadcn references for this phase

- Stats block category: https://www.shadcn.io/blocks/stats
- Empty State block category: https://www.shadcn.io/blocks/empty-state
- Skeleton block category: https://www.shadcn.io/blocks/skeleton
- Badge primitive: https://ui.shadcn.com/docs/components/badge
- Alert primitive: https://ui.shadcn.com/docs/components/alert
- Tooltip primitive: https://ui.shadcn.com/docs/components/tooltip

Also open `reference/SHADCN_BLOCK_LINKS.md` before implementation.

## Tests

Frontend:

- indicator hidden when no domain selected
- indexing state renders
- stale state renders
- no admin fields visible
- polling stops on unmount/domain switch

Backend:

- user-safe route excludes admin-only fields
- domain access rules enforced

## Validation

```bash
python -m pytest -q
cd client
npm run lint
npm run build
```

## Human inspection gate

Inspect:

- Is the indicator useful but not noisy?
- Does it avoid admin details?
- Does it preserve chat/source navigation behavior?
- Does it avoid extra polling loops?
