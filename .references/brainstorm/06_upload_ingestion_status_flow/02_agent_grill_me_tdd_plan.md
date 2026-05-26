# Upload And Readiness Hardening - Grill Me + TDD Plan

## Mission

Implement a lean upload-status and readiness hardening pass with strict behavior checks and no frontend dependency on LightRAG internals.

## Shared Assumptions To Challenge

- Job `succeeded` does not always mean document is fully indexed remotely.
- WebUI should read backend-owned status abstraction, not provider-specific IDs.
- Readiness must reflect real dependency health, not placeholder responses.

## TDD Tracer Bullets (Vertical Slices)

### Slice A - Admin can poll in-flight ingestion status

1. **RED**: test admin can call `GET /admin/documents/{id}/ingestion-status` while doc is `indexing`.
2. **GREEN**: implement route and payload reuse.
3. **REFactor**: centralize ingestion payload builder.

Decision checkpoint:
- Is payload shape consistent with existing user ingestion-status endpoint?

### Slice B - Hide LightRAG `track_id` from ingestion payload

1. **RED**: test `track_id` is absent from ingestion-status response.
2. **GREEN**: redact from shared serializer.
3. **REFactor**: ensure redaction is localized to response, not persistence.

Decision checkpoint:
- Confirm backend still retains `track_id` for refresh logic.

### Slice C - Pending-status poller advances indexing docs

1. **RED**: test `poll_lightrag_statuses()` transitions indexing doc to ready when adapter reports ready.
2. **GREEN**: ensure recurring process exists and runs task.
3. **REFactor**: keep interval configurable via settings.

Decision checkpoint:
- Poller runs independently from queue worker and does not block ingestion jobs.

### Slice D - Strict readiness dependency matrix

1. **RED**: tests for
   - healthy all services
   - lightrag unhealthy
   - registry missing
   - redis unhealthy in queue mode
2. **GREEN**: implement readiness service and route wiring.
3. **REFactor**: enforce consistent `status/services` shape for both 200/503.

Decision checkpoint:
- Confirm strict default-domain policy: readiness fails when default LightRAG domain health fails.

## Grill-Me Questions During Implementation

- Does any endpoint still force frontend to know `track_id`?
- Can admin status UI progress without calling mutating refresh endpoint?
- Are we exposing identical readiness payload shape on 200 and 503?
- Is queue mode behavior explicit when Redis is down?
- Do docs explain when to run worker vs status-poller?

## Acceptance Gate

- Upload flow supports:
  - `POST /admin/documents/upload`
  - `GET /jobs/{job_id}`
  - `GET /admin/documents/{document_id}/ingestion-status`
- `status-poller` is wired in compose and interval-configurable.
- `/health/readiness` reports `services` map and fails strict default-domain checks.
- Tests describe behavior via public routes/tasks, not internals.
- API/deployment docs updated with new polling and readiness contracts.
