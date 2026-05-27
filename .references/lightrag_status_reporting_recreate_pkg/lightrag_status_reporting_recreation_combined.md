# LightRAG Status Reporting Recreation Documentation Package

Generated: 2026-05-26


---

# README.md

# LightRAG-Style Status Reporting Recreation Package

Generated: 2026-05-26

Repository reviewed:

```text
https://github.com/HKUDS/LightRAG.git
```

## Purpose

This documentation package explains how LightRAG reports document upload and ingestion status, and how to recreate the same pattern in another codebase, such as `context_engine`.

It is written for:

- coding agents
- junior developers
- frontend developers wiring status panels
- backend developers building ingestion/job status APIs
- reviewers trying to preserve LightRAG-style UX without copying its whole internals

## Main Finding

LightRAG status reporting is not one single script. It is a coordinated backend + frontend pattern:

```text
upload/insert/scan request
  → track_id generated immediately
  → background task enqueues documents
  → doc_status storage records per-document state
  → processing pipeline updates global pipeline_status
  → WebUI polls per-document and global status APIs
  → status filters, progress dialog, health badge, and pipeline activity indicators update
```

There is no dedicated standalone CLI polling script in the current status-reporting design. The closest operational scripts in the repo are setup/release/test scripts; runtime status is exposed by API routes and consumed by WebUI components.

## Package Contents

Recommended reading order:

1. `ARCHITECTURE_OVERVIEW.md`
2. `BACKEND_STATUS_API_MAP.md`
3. `BACKEND_STORAGE_AND_PIPELINE_STATE.md`
4. `WEBUI_STATUS_REFERENCE_MAP.md`
5. `UX_BEHAVIOR_TO_RECREATE.md`
6. `RECREATE_IMPLEMENTATION_PLAN.md`
7. `CONCRETE_CODING_TASKS.md`
8. `API_CONTRACTS.md`
9. `FRONTEND_COMPONENT_CONTRACTS.md`
10. `TEST_PLAN.md`
11. `CODING_AGENT_PROMPT.md`
12. `ADRS_TO_WRITE.md`

## Short Version for Coding Agent

Recreate this pattern:

```text
POST upload returns track_id
GET /track_status/{track_id} returns per-upload document states
GET /pipeline_status returns global job/progress/messages
GET /paginated returns document table rows + status counts
GET /health returns pipeline_active for high-level UI polling
Frontend polls:
  - /health at normal cadence
  - /paginated every 5s when active, 30s idle
  - /pipeline_status every 2s while dialog open
  - /track_status/{track_id} when tracking a specific upload batch
```


---

# ARCHITECTURE_OVERVIEW.md

# Architecture Overview

## What LightRAG Status Reporting Solves

LightRAG needs to give users immediate feedback after upload while ingestion continues in the background.

The status design separates two user questions:

1. **What happened to my upload?**
   - Answered by `track_id` and `/documents/track_status/{track_id}`.

2. **What is the global ingestion/indexing pipeline doing right now?**
   - Answered by `/documents/pipeline_status` and `/health`.

## High-Level Flow

```text
User uploads document
  → POST /documents/upload
  → backend saves file
  → backend generates track_id
  → backend starts background pipeline_index_file(...)
  → client receives success + track_id immediately
  → background task extracts content
  → LightRAG apipeline_enqueue_documents(..., track_id)
  → doc_status writes PENDING records
  → apipeline_process_enqueue_documents()
  → pipeline_status updates busy/job/progress/messages
  → per-document doc_status updates:
        PENDING
        PROCESSING
        PREPROCESSED
        PROCESSED
        FAILED
  → WebUI polls APIs and renders:
        document table status
        status filter counts
        pipeline active indicator
        pipeline status dialog
        upload progress
        error/details dialog
```

## Two Status Mechanisms

### 1. Per-upload tracking

```text
track_id
  → ties one upload/insert/scan batch to one or more doc_status rows
  → used for exact upload result tracking
```

### 2. Global pipeline status

```text
pipeline_status namespace
  → busy
  → scanning
  → destructive_busy
  → pending_enqueues
  → job_name
  → docs
  → batchs
  → cur_batch
  → latest_message
  → history_messages
  → cancellation_requested
```

## Why This Design Works

The design separates durable state from live operational state:

```text
doc_status
  → durable per-document processing state
  → survives process restart depending storage backend

pipeline_status
  → live operational state
  → tells the UI what the current pipeline is doing
```

That separation is the most important pattern to copy.

## Recreate in Your Codebase

Use the same conceptual boundaries:

```text
Upload route
  → returns job_id/track_id immediately

Job/document status table
  → durable per-document state

Pipeline state store
  → global active job progress

Background worker
  → owns transitions and messages

Frontend API client
  → polls status endpoints

Frontend components
  → document table, progress dialog, upload status, status filters
```


---

# BACKEND_STATUS_API_MAP.md

# Backend Status API Map

## API Endpoints to Recreate

| Endpoint | Purpose | UI consumer |
|---|---|---|
| `POST /documents/upload` | Accept file, return immediate `track_id` | Upload dialog |
| `GET /documents/track_status/{track_id}` | Show per-upload status for all docs in that upload batch | Upload batch tracker / toast / detail view |
| `GET /documents/pipeline_status` | Show global pipeline job progress and messages | Pipeline status dialog |
| `POST /documents/cancel_pipeline` | Request cancellation of active pipeline | Pipeline status dialog cancel button |
| `POST /documents/paginated` | Fetch document table rows and status counts | Document manager table |
| `GET /documents/status_counts` | Fetch aggregate counts by status | Filter badges / dashboard |
| `GET /health` | Fetch high-level backend status, including `pipeline_active` | Global health store / polling cadence |

## Endpoint Responsibilities

### `POST /documents/upload`

Responsibilities:

```text
validate file
sanitize filename
reject conflicting filename/status when appropriate
write file to input/upload directory
generate track_id
reserve enqueue slot
schedule background task
return InsertResponse(status, message, track_id)
```

Do **not** wait for ingestion to complete.

### `GET /documents/track_status/{track_id}`

Responsibilities:

```text
query doc_status storage for all docs with track_id
map each record to DocStatusResponse
return TrackStatusResponse:
  track_id
  documents[]
  total_count
  status_summary
```

This endpoint answers: “What happened to the work initiated by my upload?”

### `GET /documents/pipeline_status`

Responsibilities:

```text
read shared pipeline_status namespace
copy mutable state to normal dict
truncate history_messages to safe max length
format job_start timestamp
include update_status flags if available
return PipelineStatusResponse
```

This endpoint answers: “What is the pipeline doing right now?”

### `POST /documents/paginated`

Responsibilities:

```text
query doc_status rows with page, page_size, sort field, sort direction
query status counts in parallel
return documents + pagination + status_counts
```

This endpoint powers the main document table and status filter counts.

### `GET /health`

Responsibilities:

```text
return backend health/configuration
include pipeline_busy
include pipeline_active
include pipeline_scanning
include pipeline_destructive_busy
include pipeline_pending_enqueues
```

This endpoint is used by the WebUI to keep global health and polling cadence synchronized.

## Recommended Status API Contract for Reimplementation

```python
class InsertResponse(BaseModel):
    status: Literal["success", "partial_success", "failure"]
    message: str
    track_id: str

class DocStatusResponse(BaseModel):
    id: str
    content_summary: str
    content_length: int
    status: Literal[
        "pending",
        "processing",
        "preprocessed",
        "processed",
        "failed",
    ]
    created_at: str
    updated_at: str
    track_id: str | None = None
    chunks_count: int | None = None
    error_msg: str | None = None
    metadata: dict[str, Any] | None = None
    file_path: str

class TrackStatusResponse(BaseModel):
    track_id: str
    documents: list[DocStatusResponse]
    total_count: int
    status_summary: dict[str, int]

class PipelineStatusResponse(BaseModel):
    autoscanned: bool = False
    busy: bool = False
    job_name: str = "-"
    job_start: str | None = None
    docs: int = 0
    batchs: int = 0
    cur_batch: int = 0
    request_pending: bool = False
    cancellation_requested: bool | None = None
    latest_message: str = ""
    history_messages: list[str] | None = None
    update_status: dict[str, Any] | None = None
```

## Status Values

Recommended canonical values:

```text
pending       accepted, not yet processed
processing    actively being parsed/chunked/indexed
preprocessed  parsed/chunked but waiting for final graph/vector processing
processed     fully usable for retrieval
failed        terminal failure, error_msg explains why
```

If your backend has more granular states, group them for the UI:

```text
parsing/analyzing/preprocessed → analyzing
processing                     → processing
pending                        → pending
processed                      → processed
failed                         → failed
```


---

# BACKEND_STORAGE_AND_PIPELINE_STATE.md

# Backend Storage and Pipeline State

## Durable Document Status

LightRAG stores per-document processing state in `doc_status` storage.

Implementations exist for multiple storage backends, including JSON, PostgreSQL, Redis, MongoDB, and others.

The key pattern is:

```text
doc_status row/document
  id
  content_summary
  content_length
  file_path
  status
  created_at
  updated_at
  track_id
  chunks_count
  chunks_list
  error_msg
  metadata
  content_hash
```

## Track ID

A `track_id` groups one upload/insert/scan request to the status rows it created.

LightRAG-style format:

```text
{prefix}_{YYYYMMDD_HHMMSS}_{8-char-uuid}
```

Examples:

```text
upload_20260526_143010_ab12cd34
insert_20260526_143011_6f9a2b10
scan_20260526_143020_9c8d7e6f
enqueue_20260526_143030_1a2b3c4d
```

Prefixes to preserve:

```text
upload
insert
scan
enqueue
```

## Live Pipeline Status

`pipeline_status` is a shared live state namespace.

Recommended fields:

```text
autoscanned
busy
destructive_busy
scanning
scanning_exclusive
pending_enqueues
job_name
job_start
docs
batchs
cur_batch
request_pending
cancellation_requested
latest_message
history_messages
```

## Why Track ID and Pipeline Status Are Both Needed

Do not collapse these concepts.

| Concept | Scope | Persistence | UI use |
|---|---|---|---|
| `track_id` | one upload/insert/scan batch | durable through doc_status | exact result of a user action |
| `pipeline_status` | global pipeline worker state | live/shared state | progress dialog and active indicator |

## Required State Transitions

```text
Accepted upload
  → doc_status pending

Worker starts document
  → doc_status processing
  → pipeline_status.busy true
  → pipeline_status.latest_message "Processing document..."

Parser/chunker completed
  → doc_status preprocessed or processing with chunks_count

Graph/vector indexing completed
  → doc_status processed

Exception
  → doc_status failed
  → error_msg set
  → pipeline_status.latest_message set

Pipeline complete
  → pipeline_status.busy false
  → latest_message "Document processing pipeline completed"
```

## Concurrency Flags to Copy

LightRAG’s newer pattern includes more than `busy`.

Recommended flags:

```text
busy
  true while pipeline processing or destructive jobs run

destructive_busy
  true while clear/delete operations can drop storage or remove files

scanning
  true during scan lifecycle

scanning_exclusive
  true only during scan classification phase

pending_enqueues
  number of accepted upload/insert requests whose background enqueue has not written doc_status yet

request_pending
  tells the processing loop to pick up new docs after current batch
```

## Practical Simpler Version

For a smaller codebase, start with:

```text
busy
pending_enqueues
request_pending
cancellation_requested
latest_message
history_messages
```

Add `destructive_busy` and `scanning_exclusive` if you support clear/delete/scan concurrently with upload.

## Storage Interface to Recreate

```python
class DocStatusRepository:
    async def create_pending(
        self,
        doc_id: str,
        file_path: str,
        content_summary: str,
        content_length: int,
        track_id: str,
        metadata: dict,
    ) -> None: ...

    async def update_status(
        self,
        doc_id: str,
        status: DocStatus,
        *,
        chunks_count: int | None = None,
        error_msg: str | None = None,
        metadata_patch: dict | None = None,
    ) -> None: ...

    async def get_docs_by_track_id(
        self,
        track_id: str,
    ) -> dict[str, DocProcessingStatus]: ...

    async def get_docs_paginated(
        self,
        status_filter: DocStatus | None,
        status_filters: list[DocStatus] | None,
        page: int,
        page_size: int,
        sort_field: str,
        sort_direction: str,
    ) -> tuple[list[tuple[str, DocProcessingStatus]], int]: ...

    async def get_all_status_counts(self) -> dict[str, int]: ...
```

## Pipeline State Interface to Recreate

```python
class PipelineStatusStore:
    async def get(self) -> PipelineStatus: ...
    async def update(self, patch: dict[str, Any]) -> None: ...
    async def append_message(self, message: str) -> None: ...
    async def acquire_enqueue_slot(self) -> None: ...
    async def release_enqueue_slot(self) -> None: ...
    async def acquire_destructive_busy(self) -> bool: ...
    async def request_cancel(self) -> None: ...
```

## Implementation Note for Multi-Process Servers

If the app runs with multiple worker processes, in-memory dicts are not enough. Use one of:

```text
Redis
database row/table
multiprocessing manager
file lock + JSON
```

For `context_engine`, Redis + PostgreSQL is likely cleaner:

```text
PostgreSQL → durable document/job statuses
Redis      → live pipeline progress and fast mutable state
```


---

# WEBUI_STATUS_REFERENCE_MAP.md

# WebUI Status Reference Map

## Main Files

| File | Purpose |
|---|---|
| `lightrag_webui/src/api/lightrag.ts` | Typed API client and response types for documents, status, pipeline, track status, upload, health |
| `lightrag_webui/src/features/DocumentManager.tsx` | Main document table, status filters, polling cadence, refresh logic, upload/scan controls |
| `lightrag_webui/src/components/documents/UploadDocumentsDialog.tsx` | Upload dialog, upload progress per file, duplicate/error messaging, early activity probe trigger |
| `lightrag_webui/src/components/documents/PipelineStatusDialog.tsx` | Global pipeline progress dialog, polls `/documents/pipeline_status` every 2s, cancel button |
| `lightrag_webui/src/features/documentStatusFilters.ts` | Status grouping logic: processed/analyzing/processing/pending/failed |
| `lightrag_webui/src/stores/state.ts` | Backend health state; stores `pipelineBusy` and `pipelineActive` from `/health` |
| `lightrag_webui/src/api/lightrag.test.ts` | Tests request deduping/timeout behavior for paginated document polling |

## API Client Patterns

### Types

The WebUI defines TypeScript types for:

```text
DocActionResponse
ScanResponse
DocStatus
DocStatusResponse
TrackStatusResponse
DocumentsRequest
PaginatedDocsResponse
StatusCountsResponse
PipelineStatusResponse
LightragStatus
```

### Methods

Important status methods:

```ts
uploadDocument(file, onUploadProgress)
getTrackStatus(trackId)
getPipelineStatus()
cancelPipeline()
getDocumentsPaginated(request)
getDocumentsPaginatedWithTimeout(request, timeoutMs)
getDocumentStatusCounts()
checkHealth()
```

### Request Deduping Pattern

The API client deduplicates in-flight paginated document requests using:

```text
request key = JSON.stringify(DocumentsRequest)
Map<requestKey, { controller, promise, subscriberCount }>
```

Why copy this:

- React StrictMode can double-mount effects.
- Multiple polling paths can overlap.
- Without dedupe, the WebUI can issue duplicate `/documents/paginated` calls.

## DocumentManager Behavior

### State Owned

```text
currentPageDocs
pagination
statusCounts
statusFilter
sortField/sortDirection
selectedDocIds
isRefreshing
pipelineActive
pollingIntervalRef
activeRefreshPromiseRef
pendingRefreshRequestRef
lastPaginatedAtRef
probeTimersRef
```

### Polling Cadence

```text
if current tab is not Documents:
  stop polling

if backend unhealthy:
  stop polling

if active documents exist OR pipelineActive:
  poll /documents/paginated every 5s

else:
  poll /documents/paginated every 30s
```

### Throttle Gate

All auto-refresh entrances funnel through a throttled refresh to enforce a minimum 2s wall-clock interval.

Copy the idea, not necessarily the exact implementation.

### Activity Probe

After upload or scan starts, the UI performs a short burst of `/health` checks until `pipelineActive` flips true. Then normal polling takes over.

Why this matters:

- Upload returns before doc rows appear.
- If the UI waits for normal 30s idle polling, users think nothing happened.
- Activity probe bridges the gap between "upload accepted" and "doc_status row visible."

## UploadDocumentsDialog Behavior

The dialog:

```text
sorts files before upload
uploads sequentially
shows per-file upload progress
maps HTTP 409 duplicate errors to user-friendly duplicate message
calls onUploadBatchAccepted once after first successful file is accepted
calls onDocumentsUploaded after at least one successful upload
```

Important UX distinction:

```text
upload progress == file transfer progress
processing progress == background ingestion/indexing progress
```

Do not confuse these.

## PipelineStatusDialog Behavior

The dialog:

```text
opens on demand
polls /documents/pipeline_status every 2s only while open
shows busy/request_pending/cancellation state
shows job_name, job_start, cur_batch/batchs
shows history_messages
auto-scrolls unless user manually scrolls away
lets user request cancellation when busy
```

## Status Filter Behavior

Use these UI buckets:

```text
processed
analyzing
processing
pending
failed
all
```

Map backend statuses:

```text
preprocessed/parsing/analyzing → analyzing
processing                     → processing
pending                        → pending
processed                      → processed
failed                         → failed
```

## Backend Health Store Behavior

The global backend store calls `/health` and stores:

```text
health
status
pipelineBusy
pipelineActive
lastCheckTime
message
messageTitle
```

`pipelineActive` is more useful than `pipelineBusy` because it includes:

```text
busy
scanning
destructive_busy
pending_enqueues > 0
```

Use `pipelineActive` for UI polling cadence.


---

# UX_BEHAVIOR_TO_RECREATE.md

# UX Behavior to Recreate

## 1. Upload Feedback Has Two Phases

### Phase A: File transfer

Displayed in upload dialog.

```text
0% → 100% upload progress
```

This only means the server accepted the file.

### Phase B: Background processing

Displayed in document table and pipeline dialog.

```text
pending → processing/analyzing → processed/failed
```

This means the file has been parsed, chunked, embedded, indexed, and made queryable.

## 2. Return a Tracking ID Immediately

After upload, the server returns:

```json
{
  "status": "success",
  "message": "File uploaded successfully. Processing will continue in background.",
  "track_id": "upload_20260526_143010_ab12cd34"
}
```

The frontend can use this for exact per-upload progress.

## 3. Show a Global Pipeline Activity Badge

Use `/health` or a similar status endpoint to surface:

```text
pipeline_active: true | false
pipeline_busy: true | false
pipeline_scanning: true | false
pipeline_pending_enqueues: number
```

This controls document-manager polling frequency and gives users a top-level "system is working" signal.

## 4. Show a Pipeline Status Dialog

The dialog should show:

```text
busy
request_pending
cancellation_requested
job_name
job_start
cur_batch / batchs
latest_message
history_messages
cancel button
```

Polling interval:

```text
2 seconds while dialog is open
no polling when closed
```

## 5. Show Document Status Filters

Use filter badges:

```text
All
Completed
Analyzing
Processing
Pending
Failed
```

Each badge includes count.

## 6. Show Error/Details Dialog Per Document

For each document row, expose details:

```text
track_id
metadata
error_msg
```

Add copy-to-clipboard for debugging.

## 7. Avoid Polling Storms

Copy these strategies:

```text
dedupe identical in-flight document table requests
abort timed-out requests
throttle auto-refresh to minimum interval
poll faster only when pipeline is active
poll pipeline details only when dialog is open
skip token renewal for high-frequency status endpoints
```

## 8. Handle Duplicate Uploads Clearly

LightRAG changed same-name conflicts to HTTP 409. The UI maps common 409 cases to a dedicated duplicate-file message, while other 409 reasons such as scanning/pipeline contention are shown verbatim.

Recreate:

```text
if status == 409 and detail looks like duplicate:
  show duplicate file message
else if status == 409:
  show server detail
```

## 9. Do Not Hide Background Errors

If ingestion fails asynchronously:

- upload may have returned `success`
- track status later shows document `failed`
- `error_msg` explains why

This is intentional. The UI must make async failure visible in document table and/or track-status detail.


---

# RECREATE_IMPLEMENTATION_PLAN.md

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


---

# CONCRETE_CODING_TASKS.md

# Concrete Coding Tasks

## Task 1: Add Track ID Utility

**Goal:** Generate stable upload/insert/scan tracking IDs.

**Files likely affected:**

```text
backend/utils/track_id.py
tests/test_track_id.py
```

**Implementation:**

```python
def generate_track_id(prefix: str = "upload") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}"
```

**Acceptance criteria:**

- IDs include prefix, timestamp, short UUID.
- Prefix defaults to `upload`.
- Tests verify format.

---

## Task 2: Add Document Status Model/Repository

**Goal:** Store per-document durable processing status.

**Files likely affected:**

```text
backend/models/document_status.py
backend/repositories/document_status_repository.py
migrations/*
tests/test_document_status_repository.py
```

**Acceptance criteria:**

- Can create pending rows.
- Can update status and error message.
- Can query by track_id.
- Can query paginated rows.
- Can aggregate counts.

---

## Task 3: Add Pipeline Status Store

**Goal:** Store global live pipeline progress.

**Files likely affected:**

```text
backend/services/pipeline_status_store.py
backend/core/redis.py
tests/test_pipeline_status_store.py
```

**Acceptance criteria:**

- Can initialize defaults.
- Can update busy/job/cur_batch/latest_message.
- Can append history.
- Can request cancellation.
- Can handle missing/empty state.

---

## Task 4: Wire Upload Route to Track ID and Background Task

**Goal:** Return immediately with `track_id`.

**Files likely affected:**

```text
backend/api/routes/documents.py
backend/services/document_upload_service.py
backend/workers/ingestion_tasks.py
```

**Acceptance criteria:**

- Upload returns `track_id`.
- Worker receives track_id.
- Upload does not block until ingestion completes.
- Duplicate/conflict returns 409 with useful detail.

---

## Task 5: Implement Track Status Endpoint

**Goal:** Poll exact upload batch.

**Route:**

```text
GET /documents/track_status/{track_id}
```

**Acceptance criteria:**

- Returns docs associated with track_id.
- Includes total_count and status_summary.
- Works when no docs found.

---

## Task 6: Implement Pipeline Status Endpoint

**Goal:** Show global progress/messages.

**Route:**

```text
GET /documents/pipeline_status
```

**Acceptance criteria:**

- Returns busy/job/progress/messages.
- Truncates long history safely.
- Formats timestamps.
- Requires auth.

---

## Task 7: Implement Paginated Documents Endpoint

**Goal:** Feed document table and filter counts.

**Route:**

```text
POST /documents/paginated
```

**Acceptance criteria:**

- Supports status_filter/status_filters.
- Supports page/page_size.
- Supports sort field/direction.
- Returns status_counts.

---

## Task 8: Implement Health Pipeline Fields

**Goal:** Let WebUI know whether to poll fast.

**Route:**

```text
GET /health
```

**Add fields:**

```text
pipeline_busy
pipeline_active
pipeline_scanning
pipeline_destructive_busy
pipeline_pending_enqueues
```

**Acceptance criteria:**

- `pipeline_active` is true if any active/pending pipeline condition exists.
- UI can use it for polling cadence.

---

## Task 9: Build Frontend API Client

**Goal:** Match LightRAG WebUI API client.

**Files likely affected:**

```text
client/src/api/documents.ts
client/src/types/status.ts
```

**Acceptance criteria:**

- Typed methods exist for all status APIs.
- Auth headers are included.
- High-frequency endpoints do not trigger expensive auth refresh if your auth layer supports skip lists.

---

## Task 10: Build DocumentManager

**Goal:** Document table with status filters and smart polling.

**Acceptance criteria:**

- Shows filters: all/completed/analyzing/processing/pending/failed.
- Polls every 5s while active, 30s idle.
- Dedupe/throttle prevents polling storms.
- Manual refresh works.

---

## Task 11: Build UploadDocumentsDialog

**Goal:** Upload UI with transfer progress and async processing handoff.

**Acceptance criteria:**

- Shows per-file upload progress.
- Triggers activity probe after first accepted upload.
- Shows duplicate/409 errors clearly.
- Refreshes document list after successful upload.

---

## Task 12: Build PipelineStatusDialog

**Goal:** Global progress dialog.

**Acceptance criteria:**

- Polls pipeline status every 2s only while open.
- Shows job_name, start time, cur_batch/batchs.
- Shows latest/history messages.
- Can request cancellation.

---

## Task 13: Add Tests for Polling and Request Dedupe

**Goal:** Prevent UI from flooding backend.

**Acceptance criteria:**

- Duplicate paginated requests are deduped.
- Timeout subscriber does not abort shared request unless it is last subscriber.
- Fresh retry works after abort/timeout.


---

# API_CONTRACTS.md

# API Contracts

## Upload

```http
POST /documents/upload
Content-Type: multipart/form-data
```

Response:

```json
{
  "status": "success",
  "message": "File 'example.pdf' uploaded successfully. Processing will continue in background.",
  "track_id": "upload_20260526_143010_ab12cd34"
}
```

## Track Status

```http
GET /documents/track_status/{track_id}
```

Response:

```json
{
  "track_id": "upload_20260526_143010_ab12cd34",
  "documents": [
    {
      "id": "doc-abc",
      "content_summary": "example.pdf",
      "content_length": 12345,
      "status": "processing",
      "created_at": "2026-05-26T14:30:10Z",
      "updated_at": "2026-05-26T14:30:40Z",
      "track_id": "upload_20260526_143010_ab12cd34",
      "chunks_count": 12,
      "error_msg": null,
      "metadata": {},
      "file_path": "example.pdf"
    }
  ],
  "total_count": 1,
  "status_summary": {
    "processing": 1
  }
}
```

## Pipeline Status

```http
GET /documents/pipeline_status
```

Response:

```json
{
  "autoscanned": false,
  "busy": true,
  "job_name": "indexing files",
  "job_start": "2026-05-26T14:30:11Z",
  "docs": 4,
  "batchs": 2,
  "cur_batch": 1,
  "request_pending": false,
  "cancellation_requested": false,
  "latest_message": "Processing batch 1 of 2",
  "history_messages": [
    "Starting document processing pipeline",
    "Processing batch 1 of 2"
  ],
  "update_status": {}
}
```

## Paginated Documents

```http
POST /documents/paginated
Content-Type: application/json
```

Request:

```json
{
  "status_filter": null,
  "status_filters": ["preprocessed", "processing"],
  "page": 1,
  "page_size": 50,
  "sort_field": "updated_at",
  "sort_direction": "desc"
}
```

Response:

```json
{
  "documents": [],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 0,
    "total_pages": 0,
    "has_next": false,
    "has_prev": false
  },
  "status_counts": {
    "all": 0,
    "pending": 0,
    "processing": 0,
    "preprocessed": 0,
    "processed": 0,
    "failed": 0
  }
}
```

## Status Counts

```http
GET /documents/status_counts
```

Response:

```json
{
  "status_counts": {
    "all": 10,
    "pending": 1,
    "processing": 2,
    "preprocessed": 1,
    "processed": 5,
    "failed": 1
  }
}
```

## Health

```http
GET /health
```

Status-related fields:

```json
{
  "status": "healthy",
  "pipeline_busy": true,
  "pipeline_active": true,
  "pipeline_scanning": false,
  "pipeline_destructive_busy": false,
  "pipeline_pending_enqueues": 0
}
```

## Cancel Pipeline

```http
POST /documents/cancel_pipeline
```

Response:

```json
{
  "status": "cancellation_requested",
  "message": "Pipeline cancellation has been requested. Documents will be marked as FAILED."
}
```


---

# FRONTEND_COMPONENT_CONTRACTS.md

# Frontend Component Contracts

## API Types

```ts
export type DocStatus =
  | 'pending'
  | 'processing'
  | 'preprocessed'
  | 'processed'
  | 'failed'

export type DocStatusResponse = {
  id: string
  content_summary: string
  content_length: number
  status: DocStatus
  created_at: string
  updated_at: string
  track_id?: string
  chunks_count?: number
  error_msg?: string
  metadata?: Record<string, unknown>
  file_path: string
}

export type PipelineStatusResponse = {
  autoscanned: boolean
  busy: boolean
  job_name: string
  job_start?: string
  docs: number
  batchs: number
  cur_batch: number
  request_pending: boolean
  cancellation_requested?: boolean
  latest_message: string
  history_messages?: string[]
  update_status?: Record<string, unknown>
}
```

## DocumentManager

Props:

```ts
type DocumentManagerProps = {}
```

State:

```ts
currentPageDocs: DocStatusResponse[]
pagination: PaginationInfo
statusCounts: Record<string, number>
statusFilter: 'all' | 'processed' | 'analyzing' | 'processing' | 'pending' | 'failed'
sortField: 'created_at' | 'updated_at' | 'id' | 'file_path'
sortDirection: 'asc' | 'desc'
isRefreshing: boolean
selectedDocIds: string[]
```

Responsibilities:

- fetch paginated documents
- show filters/counts
- poll based on `pipelineActive`
- open pipeline status dialog
- open upload dialog
- open document details dialog
- trigger scan/refresh/delete actions if supported

## UploadDocumentsDialog

Props:

```ts
type UploadDocumentsDialogProps = {
  onDocumentsUploaded?: () => Promise<void>
  onUploadBatchAccepted?: () => void
}
```

Responsibilities:

- let user select/drop files
- upload files sequentially or with controlled concurrency
- show transfer progress
- call `onUploadBatchAccepted` after first successful server accept
- call `onDocumentsUploaded` when batch has at least one success

## PipelineStatusDialog

Props:

```ts
type PipelineStatusDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}
```

Responsibilities:

- poll `/documents/pipeline_status` every 2s while open
- show progress and history messages
- request cancellation
- auto-scroll history unless user manually scrolls

## Status Filter Helpers

```ts
export type StatusBucket =
  | 'processed'
  | 'analyzing'
  | 'processing'
  | 'pending'
  | 'failed'

export type StatusFilter = StatusBucket | 'all'

export const getStatusBucket = (status: DocStatus): StatusBucket => {
  if (['preprocessed', 'parsing', 'analyzing'].includes(status)) {
    return 'analyzing'
  }
  if (status === 'processing') return 'processing'
  return status as StatusBucket
}
```

## Backend State Store

```ts
type BackendState = {
  health: boolean
  status: HealthResponse | null
  pipelineBusy: boolean
  pipelineActive: boolean
  lastCheckTime: number
  check: () => Promise<boolean>
}
```

Responsibilities:

- call `/health`
- update `pipelineBusy`
- update `pipelineActive`
- let DocumentManager choose polling cadence


---

# TEST_PLAN.md

# Test Plan

## Backend Tests

### Track ID

- default prefix is `upload`
- custom prefixes work
- generated IDs are unique
- generated ID format is stable

### Upload Route

- upload returns `track_id`
- background task receives `track_id`
- duplicate same-name upload returns 409
- upload during destructive busy returns 409
- upload during normal processing is allowed if your design supports pending enqueue

### Track Status Endpoint

- returns all docs with a given track ID
- returns empty list for unknown track ID
- status_summary counts correctly
- failed document includes error_msg

### Pipeline Status Store

- initializes default state
- sets busy/job/progress fields
- appends history messages
- truncates long history in API response
- supports cancellation request
- clears busy after completion

### Paginated Documents

- filters by single status
- filters by multiple statuses
- paginates correctly
- sorts only by whitelisted fields
- returns status_counts with `all`

### Health Endpoint

- reports pipeline_busy
- reports pipeline_active when pending_enqueues > 0
- reports pipeline_active during scanning
- reports pipeline_active during destructive_busy

## Frontend Tests

### API Client

- `getPipelineStatus` calls correct endpoint
- `getTrackStatus` URL-encodes track ID
- `getDocumentsPaginated` dedupes identical in-flight requests
- timed out request allows fresh retry
- one timed-out subscriber does not abort shared request if another subscriber remains

### DocumentManager

- uses 5s polling when pipelineActive or active docs exist
- uses 30s polling when idle
- stops polling when tab inactive/unmounted
- manual refresh works
- status filters show correct counts

### UploadDocumentsDialog

- shows per-file progress
- maps duplicate 409 to duplicate-file message
- calls `onUploadBatchAccepted` after first successful upload
- calls `onDocumentsUploaded` after successful batch
- rejected files show error state

### PipelineStatusDialog

- polls every 2s only when open
- stops polling when closed
- renders job_name, job_start, cur_batch/batchs
- renders history messages
- cancel button calls cancel endpoint
- cancel button disabled when not busy or already cancelling

## End-to-End Smoke Test

```text
1. Start backend.
2. Open WebUI.
3. Upload one supported file.
4. Confirm upload returns quickly.
5. Confirm document table enters pending/processing/analyzing.
6. Open pipeline dialog.
7. Confirm job progress/messages update.
8. Wait for processed.
9. Confirm status counts update.
10. Upload duplicate filename.
11. Confirm duplicate message.
12. Upload bad file / force parser error.
13. Confirm failed status + error details.
```


---

# CODING_AGENT_PROMPT.md

# Coding Agent Prompt

Use this prompt to recreate LightRAG-style status reporting in another codebase.

```md
You are a senior full-stack coding agent.

Your task is to recreate the LightRAG-style document upload and ingestion status-reporting system.

Read this documentation package first:

docs/status-reporting-recreation/

Goal:

Implement a backend + frontend status system where:

- upload returns a `track_id` immediately
- per-document processing status is durable
- global pipeline progress is visible
- users can see upload transfer progress separately from background processing progress
- users can filter document list by status
- users can open a pipeline dialog with live job messages
- users can cancel an active pipeline where supported
- frontend polling is efficient and does not flood the backend

Required backend APIs:

- POST /documents/upload
- GET /documents/track_status/{track_id}
- GET /documents/pipeline_status
- POST /documents/paginated
- GET /documents/status_counts
- POST /documents/cancel_pipeline
- GET /health with pipeline_active fields

Required frontend components:

- DocumentManager
- UploadDocumentsDialog
- PipelineStatusDialog
- DocumentStatusDetailsDialog
- status filter badges
- backend health store

Implementation rules:

- Do not block upload until ingestion finishes.
- Do not conflate upload progress with processing progress.
- Store durable document status separately from live pipeline progress.
- Use `track_id` for per-upload tracking.
- Use `pipeline_status` for global job progress.
- Do not poll every endpoint all the time.
- Poll `/pipeline_status` only when the dialog is open.
- Poll document table faster only while pipeline is active.
- Dedupe identical in-flight document-table requests.
- Surface async ingestion failures in document rows.
- Add tests for backend state transitions and frontend polling behavior.

Start with the task list in `CONCRETE_CODING_TASKS.md`.

Definition of done:

- A user can upload a file and immediately see that work was accepted.
- A user can watch document status transition to processed/failed.
- A user can open a live pipeline status dialog.
- A user can see status counts and filter documents.
- The frontend does not spam backend requests.
- Tests cover track status, pipeline status, document table polling, upload handling, and cancellation.
```


---

# ADRS_TO_WRITE.md

# ADRs to Write

## ADR-001: Track ID vs Job ID

Decision:

- Whether the system uses LightRAG-style `track_id`, existing job IDs, or both.

Recommended:

```text
Use track_id for user-facing upload/insert/scan batches.
Use internal job IDs for queue/worker implementation if needed.
```

## ADR-002: Durable Document Status Storage

Decision:

- Where per-document status lives.

Recommended:

```text
Store per-document ingestion status in PostgreSQL.
Use Redis only for live mutable pipeline progress.
```

## ADR-003: Global Pipeline Status Store

Decision:

- Where live pipeline state lives.

Recommended:

```text
Use Redis key per workspace/domain for live pipeline status.
```

## ADR-004: Polling Strategy

Decision:

- How often the frontend polls.

Recommended:

```text
Document list: 5s active, 30s idle.
Pipeline dialog: 2s only while open.
Track status: optional 2s until terminal.
Health: existing app cadence.
```

## ADR-005: Cancellation Semantics

Decision:

- What cancellation does to already-processing documents.

Recommended:

```text
Cancellation sets a flag. Worker checks between major processing units.
Unprocessed docs become failed/cancelled with clear error_msg.
```

## ADR-006: Multi-Workspace / Multi-Domain Status

Decision:

- Whether status is global or per domain/workspace.

Recommended for context_engine:

```text
Pipeline status should be domain-scoped:
pipeline_status:{lightrag_domain_id}
```

## ADR-007: Upload Conflicts and Duplicate Handling

Decision:

- Whether same-name files are rejected or versioned.

Recommended:

```text
Reject same-name conflicts with HTTP 409 unless versioning is explicitly supported.
```
