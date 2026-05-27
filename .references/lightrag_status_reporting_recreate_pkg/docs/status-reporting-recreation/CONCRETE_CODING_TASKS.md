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
