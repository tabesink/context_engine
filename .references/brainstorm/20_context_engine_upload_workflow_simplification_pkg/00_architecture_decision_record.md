# ADR: Low-Entropy Upload and Status Workflow

## Status

Accepted for phased implementation.

## Context

The current upload workflow has multiple status surfaces:

```text
documents.status
jobs.status
documents.metadata.lightrag.status
processing-status endpoints
ingestion-status endpoints
manual refresh-status route
backend status poller
remote LightRAG pipeline status
```

All of these can answer some version of “where is my upload?” This creates UI confusion and backend entropy.

## Decision

Adopt the following ownership model:

```text
DocumentUploadService
  Creates document + operation.

DocumentIngestionWorker
  Executes the operation.

RemoteStatusReconciler
  Polls LightRAG only for documents waiting on remote completion.

ProcessingStatusService
  Read-only UI status composer.

DocumentRetryService
  Creates a new operation for failed documents.

OperationsRepository
  Owns active work state.

DocumentRepository
  Owns document availability.
```

## Core rule

```text
Upload creates a document and one operation.
The operation owns active progress.
The document owns final/current availability.
Processing-status is the only normal UI polling surface.
Jobs/worker/poller are internal machinery.
```

## Consequences

Positive:

- UI has one normal status polling contract.
- Worker and poller responsibilities become distinct.
- Retrying failed uploads no longer depends on exposing job IDs to the user.
- LightRAG remote status is reconciled into local operation/document state instead of leaking everywhere.
- Backend state transitions can be centralized.

Tradeoffs:

- Requires compatibility with existing jobs and ingestion-status endpoints during migration.
- Requires careful test coverage because upload spans API, DB, worker, LightRAG, and polling.
- Requires UI changes to stop using old status endpoints.

## Accepted target

```text
Upload document.
Watch processing status.
Retry if failed.
Open when ready.
```
