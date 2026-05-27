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
