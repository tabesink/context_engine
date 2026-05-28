# Phase 4 — Document Processing Status UI

## Goal

Expose document ingestion/processing/indexing status to admins using normalized Context Engine status APIs.

## Scope

Allowed:

- Admin document status table.
- Upload/ingestion status rows or cards.
- Status counters.
- Failed document details.
- Retry action if backend already supports it.
- Polling while admin document panel is visible.

Not allowed:

- Replacing upload flow architecture.
- Parsing raw LightRAG document payloads in frontend.
- Showing admin-only failure details to regular users.
- Adding SSE/WebSocket.

## UI pattern

Use the Dashboard PDF Processing / File Upload / Table pattern.

Suggested stages:

```txt
queued → uploading → parsing → chunking → embedding → graph/indexing → indexed
                                                ↘ failed
```

Keep these as display labels mapped from normalized backend `stage`/`status`.

## Components

Suggested:

```txt
client/src/components/settings/documents/DocumentProcessingOverview.tsx
client/src/components/settings/documents/DocumentProcessingTable.tsx
client/src/components/settings/documents/DocumentStatusChip.tsx
client/src/components/settings/documents/DocumentFailureDetails.tsx
client/src/components/settings/documents/DocumentRetryAction.tsx
```

If generic `StatusChip` exists from Phase 0, reuse it.

## API usage

Use:

- `GET /admin/lightrag/domains/{domain_id}/documents/processing-status`
- `GET /documents/{document_id}/processing-status` for details if needed

## Frontend state

Use the status store/hook from Phase 2/3. Do not create a second polling loop.

Suggested call shape:

```ts
useDomainProcessingStatus(domainId, {
  scope: "admin",
  enabled: isAdmin && activeSettingsRoute === "documents",
});
```

## Table columns

Minimum:

- Document
- Domain
- Status
- Stage
- Chunks
- Assets
- Last updated
- Message/error
- Actions


## shadcn references for this phase

- Dashboard PDF Processing: https://www.shadcn.io/blocks/dashboard-pdf-processing
- File Upload block category: https://www.shadcn.io/blocks/file-upload
- Tables block category: https://www.shadcn.io/blocks/tables
- Table primitive: https://ui.shadcn.com/docs/components/table
- Badge primitive: https://ui.shadcn.com/docs/components/badge
- Progress primitive: https://ui.shadcn.com/docs/components/progress
- Skeleton primitive: https://ui.shadcn.com/docs/components/skeleton

Also open `reference/SHADCN_BLOCK_LINKS.md` before implementation.

## Tests

Frontend:

- renders empty state
- renders processing rows
- renders failed row with details
- hides retry if action unavailable
- polling disabled when route not visible

Backend:

- route pagination/filter tests if new filters are added

## Validation

```bash
cd client
npm run lint
npm run build
```

## Human inspection gate

Inspect:

- Are statuses clear without exposing raw LightRAG internals?
- Are failure states actionable?
- Is the UI compact enough?
- Does polling stop when the screen is not visible?
