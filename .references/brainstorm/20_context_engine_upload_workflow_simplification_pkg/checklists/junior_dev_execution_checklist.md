# Junior Developer Execution Checklist

## Before any phase

```text
[ ] Pull latest main.
[ ] Run tests.
[ ] Run migrations to head.
[ ] Create a branch for one phase only.
[ ] Read 03_state_ownership_contract.md.
[ ] Read 06_phase_by_phase_implementation_plan.md.
```

## Phase 1

```text
[ ] Upload UI polls processing-status only.
[ ] New UI does not use ingestion-status.
[ ] New UI does not use jobs as primary progress.
[ ] Processing response has enough fields for UI.
```

## Phase 2

```text
[ ] Operation-compatible fields added to jobs.
[ ] ORM updated.
[ ] Existing workers still work.
[ ] Upload response includes operation_id/job_id and status_url.
```

## Phase 3

```text
[ ] Status transitions centralized.
[ ] Worker uses status service.
[ ] Poller uses status service.
[ ] Routes do not directly mutate multiple status fields.
```

## Phase 4

```text
[ ] metadata.lightrag.status is not authoritative.
[ ] Remote status is only diagnostic/echo.
[ ] Operation/document status drive UI.
```

## Phase 5

```text
[ ] Document retry endpoint exists.
[ ] UI retry uses document ID.
[ ] Job retry remains admin diagnostics only.
```

## Final

```text
[ ] Domain lifecycle card only exposes Start/Stop/Delete.
[ ] Documents page owns upload/status/retry.
[ ] Jobs/operations page is admin diagnostics.
```
