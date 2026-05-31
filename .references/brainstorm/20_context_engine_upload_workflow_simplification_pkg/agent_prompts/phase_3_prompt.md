# Phase 3 Prompt — Centralize Status Transitions

Implement Phase 3 only.

Goal:

```text
All upload/ingestion state transitions pass through one DocumentIngestionStatusService.
```

Tasks:

```text
1. Add/refactor DocumentIngestionStatusService.
2. Add methods: mark_queued, mark_running, mark_waiting_remote, mark_succeeded, mark_failed, reconcile_remote_status.
3. Update upload service to use mark_queued.
4. Update worker to use mark_running/succeeded/failed/waiting_remote.
5. Update poller/manual refresh to use reconcile_remote_status.
6. Keep ProcessingStatusService read-only/composition focused.
7. Add status transition tests.
```

Do not change UI in this phase except as required by tests.
