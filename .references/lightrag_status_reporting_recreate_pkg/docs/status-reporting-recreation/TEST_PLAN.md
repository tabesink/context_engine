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
