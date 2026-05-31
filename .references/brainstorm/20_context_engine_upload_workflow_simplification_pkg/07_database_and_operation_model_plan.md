# Database and Operation Model Plan

## Minimal DB change

Do not rename `jobs` immediately. Add operation-compatible fields first.

```text
jobs
  id
  kind                      existing; later operation_type
  status                    existing
  document_id               existing compatibility field
  resource_type             new: document | domain | provider | system
  resource_id               new
  stage                     new
  message                   new
  progress_current          new
  progress_total            new
  error_message             existing
  metadata                  existing
  created_at                existing
  updated_at                existing
  started_at                new if not present
  finished_at               new if not present
```

## Upload-specific operation values

```text
kind/type = document_ingest
resource_type = document
resource_id = documents.id
status = queued | running | succeeded | failed | canceled
stage = queued | saving | parsing | extracting_assets | indexing_lightrag | waiting_remote | complete | failed
```

## Document status values

```text
uploaded
indexing
ready
failed
deleted
```

## Why keep jobs table name initially?

```text
Lower migration risk.
Existing worker, routes, and tests may depend on jobs.
Operation terminology can be introduced at service/API level first.
Physical rename can happen later if worth it.
```

## Later optional rename

```text
jobs -> operations
JobRow -> OperationRow
JobStatus -> OperationStatus
/jobs -> /operations
```

This is optional. The important simplification is the concept and ownership, not the physical table name.
