# Frontend UI Wiring Plan

## Documents surface

The Documents surface owns upload and document processing status.

```text
Documents page
  ├─ Upload document button
  ├─ Domain selector
  ├─ Upload progress / processing table
  ├─ Status chip
  ├─ Stage/message text
  ├─ Retry button if can_retry
  └─ Open/View button if ready
```

## Domain lifecycle surface

The domain lifecycle surface should not own uploads.

Allowed actions:

```text
Start
Stop
Delete
```

Do not expose here:

```text
Upload Documents
View Documents
View Logs
Repair
Recreate
Regenerate
Purge
Manual Refresh Status
```

## Status chip mapping

```text
queued       -> Queued
indexing     -> Processing
ready        -> Ready
failed       -> Failed
deleted      -> Deleted
```

## Stage/message examples

```text
queued              Waiting for worker
parsing             Parsing document
extracting_assets   Extracting figures and tables
indexing_lightrag   Indexing in LightRAG
waiting_remote      Waiting for LightRAG to finish indexing
complete            Ready
failed              Failed
```

## Polling rules

Use processing-status only.

```text
After upload:
  poll status_url every 2 seconds while queued/indexing/running/waiting_remote

Stop polling when:
  document.status in ready | failed | deleted

Domain board:
  poll admin domain processing-status every 3 seconds while domain.is_busy=true
  poll every 15-30 seconds or on manual refresh when idle
```

## Retry rule

When `can_retry=true`, call:

```text
POST /admin/documents/{document_id}/retry-ingestion
```

Do not call job retry from normal document UI.
