# State Ownership Matrix

The cleanup should reduce duplicate status ownership without removing useful operational visibility.

## Recommended ownership rules

| State | Canonical source of truth | Derived/cached views | Cleanup rule |
|---|---|---|---|
| User identity/auth | Auth tables/session/JWT config | Frontend auth store | Do not duplicate permission logic in UI. UI gates are convenience only. |
| Admin role | Backend authz/dependencies | Frontend conditional rendering | Backend remains source of truth. |
| Domain metadata | Domain manifest/registry/database as implemented | Domain list API | Pick one persisted source and document it. |
| Domain lifecycle transition | Lifecycle repository/state table | Admin status UI | Use for archiving, failed destructive transition, archived. |
| Domain runtime health | Probe/status poller result with timestamp | Domain cards/status API | Health is derived, not desired state. Always include freshness. |
| Docker container state | Docker runtime | Backend health projection | Do not make frontend infer Docker state. |
| LightRAG reachability | Reachability service/probe | Domain health API | Keep distinct from metadata existence. |
| Domain artifacts/env/compose | Generated files from settings/model snapshots | Not a status source | Regenerate/repair should own these. |
| Document metadata | Document registry row | Document list/detail API | Keep document registry as user-facing source. |
| Document ingestion execution | Job row | Jobs API/admin table | Job = execution attempt, not document identity. |
| Document ingestion status | Projection from document + latest job + processing status | `/ingestion-status` response | Define enum and staleness semantics. |
| Processing progress cache | Cache/service | Status response detail | Cache is non-authoritative unless backed by durable job/document state. |
| Retrieval evidence | Retrieval service response schema | Workspace/context panel | One canonical `Evidence` object should feed all UI surfaces. |
| Workspace tree selection | Frontend UI state | URL/query params optionally | Selection is UI state, not backend truth. |
| Provider/API key settings | Backend settings storage/secret crypto | Settings UI | Never duplicate secrets in frontend state. |

## Status model recommendation

Use three separate but composable concepts:

### 1. Desired/admin lifecycle state

Examples:

```text
active
stopped
archiving
archived
purging
failed
```

This is persisted and reflects admin intent or destructive transition state.

### 2. Runtime health state

Examples:

```text
healthy
starting
unreachable
running_unverified
stopped
error
unknown
```

This is derived from Docker/LightRAG reachability and should include `checked_at`.

### 3. Document processing state

Examples:

```text
uploaded
queued
processing
indexed
failed
retrying
```

This is a projection from document registry + job state + processing details.

## Cleanup tasks

1. Add `docs/status-semantics.md` or equivalent to the repo.
2. Audit every status endpoint and mark canonical source.
3. Add tests for status projection under failure/stale states.
4. Remove frontend-only status transformations that conflict with backend enums.
5. Ensure backend responses include timestamps for health/status where useful.
