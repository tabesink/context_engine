# 05 Rollout and Compatibility Boundary

## Current State

The backend currently exposes evidence retrieval through:

```text
POST /retrieve
```

The removed query routes are not supported:

```text
POST /query
POST /query/answer
POST /query/retrieve
```

Tests assert these routes return 404. Treat that as the compatibility boundary for the evidence panel package.

## Recommended Rollout

### Phase 1: Keep Backend Retrieve-Only

Keep `POST /retrieve` as the only evidence retrieval endpoint. It should remain a thin wrapper around the existing retrieval service.

### Phase 2: Update WebUI

Update the WebUI side panel to call:

```text
POST /retrieve
```

Do not use `/query/answer` or `/query` for the side panel.

### Phase 3: Preserve The Removed Route Boundary

Do not reintroduce `/query/retrieve` during evidence-panel work.

If a future client requires it, decide that explicitly in a separate API change. The alias must call the same service method and include tests that explain why the extra surface exists.

## API Versioning Note

Avoid adding `/api/v1/retrieve` unless the existing app already consistently uses `/api/v1`.

Follow current route style to avoid route entropy.

## Logging

The current retrieval service records queries through `LogRepository.record_query(...)`.

`/retrieve` should continue to record retrieval calls through the same service path.

## Failure Safety

Do not swallow LightRAG errors in the side panel. Convert known backend errors into clear UI messages.

## Rollback Plan

If `/retrieve` causes issues:

1. Keep backend retrieval service unchanged.
2. Fix `/retrieve` route registration, schema mismatch, or WebUI request shape.
3. Roll back the WebUI panel integration if needed.

Because the route is a thin wrapper, rollback should not require touching retrieval logic.
