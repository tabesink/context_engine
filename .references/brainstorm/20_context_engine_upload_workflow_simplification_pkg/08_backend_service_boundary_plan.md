# Backend Service Boundary Plan

## Target services

```text
DocumentUploadService
  Creates document + operation.

DocumentIngestionWorker / worker task
  Executes document_ingest operation.

DocumentIngestionStatusService
  Owns status transitions.

RemoteStatusReconciler
  Maps LightRAG remote status to local operation/document state.

ProcessingStatusService
  Builds read-only status response for UI.

DocumentRetryService
  Creates new operation for failed/retryable document.

OperationsRepository
  Persists operation/job state.

DocumentRepository
  Persists document state.
```

## Route handler rule

Route handlers should not encode status transition rules.

Bad:

```text
route sets documents.status
route sets jobs.status
route patches metadata.lightrag.status
route returns custom status calculation
```

Good:

```text
route validates request
route calls service
service calls repository/status service
route returns schema
```

## Worker rule

Worker should not directly know every document status detail.

Preferred:

```python
status.mark_running(document_id, operation_id, stage="parsing", message="Parsing document")
status.mark_running(document_id, operation_id, stage="indexing_lightrag", message="Indexing in LightRAG")
status.mark_succeeded(document_id, operation_id)
status.mark_failed(document_id, operation_id, error_message=str(exc))
```

## ProcessingStatusService rule

ProcessingStatusService should compose and present state.

It may read:

```text
document row
latest operation row
remote diagnostic snapshot
local structure readiness
```

It should not be the primary mutator of document/operation status.
