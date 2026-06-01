# Operations Visibility

Operations are the product/API vocabulary for async work. The database table may still be named `jobs`, but HTTP clients and admin UI should use operations.

## Current Contract

- Backend route family: `GET /operations`, `GET /operations/{operation_id}`, and `POST /operations/{operation_id}/retry`.
- Frontend API client: `client/src/lib/api/operations.ts`.
- Frontend admin view: `client/src/app/operations/page.tsx`.
- Navigation entry: `client/src/components/layout/AppSideRail.tsx`.

The operation response exposes:

```text
id
type
status
stage
progress
resource_type
resource_id
resource_label
actor_user_id
message
error_message
metadata
created_at
started_at
finished_at
updated_at
```

## Admin UI Behavior

The `/operations` page is intentionally a compact activity table:

- Status and resource filters call `operationsApi.list`.
- Active work is counted from `queued` and `running` operations.
- Failed `document_ingest` operations expose a retry button that calls `operationsApi.retry`.
- Progress renders as a narrow semantic track when the backend reports progress.
- Document, domain, provider, and system operations can share the same table.

## Ownership Rules

- Components should not call `/jobs`.
- Public async lifecycle language should say operation, not job.
- Keep the `jobs` table/repository name until a deliberate storage migration is planned.
- Domain lifecycle actions and document ingest/retry should continue creating operation rows.

