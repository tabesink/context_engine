# Coding Agent Review Checklist

## Architecture

```text
[ ] Does the change reduce status surface duplication?
[ ] Is processing-status the normal UI polling contract?
[ ] Is /jobs treated as admin diagnostics only?
[ ] Does operation/job own active progress?
[ ] Does document own current availability?
[ ] Is metadata.lightrag non-authoritative?
```

## Backend

```text
[ ] Route handlers are thin.
[ ] Status transitions are centralized.
[ ] Worker and poller use the same status service.
[ ] Poller only reconciles remote status.
[ ] Retry creates a new operation instead of mutating old failure history destructively.
```

## Database

```text
[ ] Migration is additive first.
[ ] Existing job rows are backfilled.
[ ] No premature jobs->operations table rename.
[ ] Indexes support resource_type/resource_id/status.
```

## UI

```text
[ ] Documents surface owns upload/status/retry.
[ ] Domain lifecycle surface owns Start/Stop/Delete only.
[ ] No Upload Documents in domain card/menu.
[ ] No View Documents in domain card/menu.
[ ] No View Logs in domain card/menu.
[ ] No raw LightRAG status as main chip.
```

## Tests

```text
[ ] Upload route test.
[ ] Processing-status test.
[ ] Worker status transition test.
[ ] Poller reconciliation test.
[ ] Retry ingestion test.
[ ] Frontend smoke path or component test.
```
