# Worker and Poller Responsibility Plan

## Worker responsibility

The worker should own local execution of the ingest operation.

```text
Worker should:
  mark operation running
  set operation stage/message
  parse document
  save local pages/sections/blocks/chunks/assets
  push chunks to LightRAG
  mark operation succeeded when fully complete
  or mark waiting_remote when LightRAG completion is asynchronous
  mark operation failed on failure
  update document.status through one status service
```

## Poller / RemoteStatusReconciler responsibility

The poller should not be a second ingest worker.

```text
Poller should:
  scan documents/operations in waiting_remote or indexing state
  ask LightRAG for remote terminal status
  map raw remote status to app-level operation/document status
  update through one status service
```

## Poller should not

```text
Do not parse documents.
Do not enqueue duplicate ingest jobs.
Do not invent separate status states.
Do not write hidden source-of-truth values into metadata.
```

## Worker/poller state flow

```text
Upload
  └─ creates operation queued

Worker starts
  ├─ operation running/parsing
  ├─ operation running/extracting_assets
  ├─ operation running/indexing_lightrag
  │
  ├─ LightRAG immediately complete
  │    └─ operation succeeded, document ready
  │
  └─ LightRAG async pending
       └─ operation running/waiting_remote, document indexing
            │
            ▼
          Poller/Reconciler
            ├─ remote ready -> operation succeeded, document ready
            └─ remote failed -> operation failed, document failed
```

## One service updates status

Create or centralize:

```text
DocumentIngestionStatusService
  mark_queued(document_id, operation_id)
  mark_running(document_id, operation_id, stage, message)
  mark_waiting_remote(document_id, operation_id, message)
  mark_succeeded(document_id, operation_id)
  mark_failed(document_id, operation_id, error_message)
  reconcile_remote_status(document_id)
```

Do not scatter transition logic across routes, worker, poller, and presenter.
