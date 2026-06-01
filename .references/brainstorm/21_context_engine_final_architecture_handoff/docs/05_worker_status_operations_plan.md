# 05 — Worker, Status, and Operations Plan

## Current Desired Mental Model

A document upload is not just an upload. It is an operation with several stages:

```text
register_upload
parse_local_structure
push_to_lightrag
poll_remote_indexing
complete
```

## Target Flow

```text
Admin uploads document
        │
        ▼
POST /admin/documents/upload
        │
        ▼
DocumentService.upload()
        │
        ├─ create document row
        ├─ create operation/job row
        ├─ enqueue worker
        └─ return document_id + operation_id + processing_status_url
                    │
                    ▼
              RQ worker task
                    │
                    ├─ stage=parse_local_structure
                    ├─ parse source file
                    ├─ save pages/sections/blocks/assets/chunks
                    │
                    ├─ stage=push_to_lightrag
                    ├─ send chunks/file to LightRAG
                    │
                    ├─ stage=poll_remote_indexing
                    └─ ready/failed
```

## Operation Statuses

Use these operation statuses:

```text
queued
running
waiting_remote
succeeded
failed
cancelled
```

## Document Statuses

Use these document statuses:

```text
uploaded
processing
ready
failed
```

Keep detailed state in `stage`, not by inventing many top-level statuses.

## Stage-to-UI Mapping

| Stage | UI Label |
|---|---|
| `register_upload` | Registering upload |
| `parse_local_structure` | Parsing document |
| `push_to_lightrag` | Sending to LightRAG |
| `poll_remote_indexing` | Waiting for LightRAG indexing |
| `complete` | Ready |
| `failed` | Failed |

## Admin Operations Page

The Operations page should show:

```text
Status
Type
Resource
Stage
Progress
Triggered by
Created at
Updated at
Error, if any
```

## Retry Rules

Retry should be explicit and conservative.

```text
Only failed operations can be retried.
Only admins can retry.
Retry creates a new operation or clearly marks retry_count.
Previous error should be preserved in metadata/history.
```

## Polling Rules

Frontend polling:

```text
Document page polls /documents/{id}/processing-status.
Admin operations page polls /operations.
Do not poll both for the same UI panel unless necessary.
```

Worker polling:

```text
Status poller updates waiting_remote operations/documents.
Poller should be idempotent.
Poller should not create duplicate operations.
```
