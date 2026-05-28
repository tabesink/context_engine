# Recreate Implementation Plan

## Phase 0: Decide Status Scope

### Goal

Decide which parts to recreate.

Minimum viable LightRAG-style status reporting:

```text
upload returns track_id
doc_status table
pipeline_status store
/paginated table endpoint
/pipeline_status endpoint
frontend document manager polling
pipeline status dialog
```

Optional:

```text
/track_status/{track_id}
/status_counts
/cancel_pipeline
activity probe
in-flight request dedupe
scan/reprocess/clear/delete support
```

## Phase 1: Backend Data Model

### Add durable document/job status model

Example SQL table:

```sql
CREATE TABLE document_processing_status (
  id TEXT PRIMARY KEY,
  document_id TEXT NULL,
  content_summary TEXT NOT NULL DEFAULT '',
  content_length INTEGER NOT NULL DEFAULT 0,
  file_path TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  track_id TEXT NULL,
  chunks_count INTEGER NULL,
  error_msg TEXT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX ix_doc_status_track_id ON document_processing_status(track_id);
CREATE INDEX ix_doc_status_status_updated ON document_processing_status(status, updated_at DESC);
```

### Add live pipeline state

For small app:

```text
Redis key: pipeline_status:{workspace}
```

For DB-only app:

```sql
CREATE TABLE pipeline_status (
  workspace TEXT PRIMARY KEY,
  status_json JSONB NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

## Phase 2: Backend Status APIs

Implement:

```text
POST /documents/upload
GET /documents/track_status/{track_id}
GET /documents/pipeline_status
POST /documents/paginated
GET /documents/status_counts
POST /documents/cancel_pipeline
GET /health
```

## Phase 3: Background Worker Transitions

Worker must call status methods.

Pseudo-flow:

```python
async def process_document(doc_id: str, track_id: str):
    await doc_status.update_status(doc_id, "processing")
    await pipeline.append_message(f"Processing document {doc_id}")

    try:
        parsed = await parse(...)
        chunks = await chunk(...)
        await doc_status.update_status(
            doc_id,
            "preprocessed",
            chunks_count=len(chunks),
        )

        await embed_and_index(chunks)
        await doc_status.update_status(doc_id, "processed")

    except Exception as exc:
        await doc_status.update_status(
            doc_id,
            "failed",
            error_msg=str(exc),
        )
        await pipeline.append_message(f"Failed document {doc_id}: {exc}")
```

## Phase 4: Frontend API Client

Create typed API methods:

```ts
uploadDocument(file, onUploadProgress)
getTrackStatus(trackId)
getPipelineStatus()
cancelPipeline()
getDocumentsPaginated(request)
getDocumentStatusCounts()
checkHealth()
```

Use a shared HTTP client with auth headers.

## Phase 5: Frontend Store

Global backend status store:

```ts
type BackendState = {
  health: boolean
  pipelineBusy: boolean
  pipelineActive: boolean
  status: HealthResponse | null
  check: () => Promise<boolean>
}
```

Document manager state:

```ts
currentPageDocs
pagination
statusCounts
statusFilter
sortField
sortDirection
isRefreshing
selectedDocIds
```

## Phase 6: Frontend Components

Build components:

```text
DocumentManager
UploadDocumentsDialog
PipelineStatusDialog
DocumentStatusDetailsDialog
StatusFilterBadges
PaginationControls
```

## Phase 7: Polling Behavior

Implement:

```text
health poll: normal cadence
document table poll:
  5s if pipelineActive or active docs exist
  30s if idle
pipeline dialog poll:
  2s only while open
track status poll:
  optional; every 2s for a specific upload until terminal statuses
```

## Phase 8: Tests

Add tests for:

```text
track_id generation
upload returns track_id
doc_status transitions
pipeline_status mutation
track status endpoint
paginated endpoint
status count endpoint
frontend status filter grouping
frontend paginated request dedupe
pipeline dialog polling cleanup
upload dialog 409 handling
```
