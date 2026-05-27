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
