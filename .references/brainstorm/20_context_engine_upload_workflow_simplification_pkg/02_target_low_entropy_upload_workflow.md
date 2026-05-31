# Target Low-Entropy Upload Workflow

## Target flow

```text
Admin uploads file
   │
   ▼
POST /admin/documents/upload
   │
   ▼
Create Document
   status = uploaded
   │
   ▼
Create Operation
   type = document_ingest
   resource_type = document
   resource_id = document.id
   status = queued
   stage = queued
   │
   ▼
Worker runs operation
   │
   ├─ operation.status = running
   ├─ operation.stage = parsing | extracting_assets | indexing_lightrag | waiting_remote
   ├─ document.status = indexing
   │
   ├─ success:
   │     operation.status = succeeded
   │     operation.stage = complete
   │     document.status = ready
   │
   └─ failure:
         operation.status = failed
         document.status = failed
```

## Product flow

```text
Upload document.
Watch processing status.
Retry if failed.
Open when ready.
```

## UI polling path

After upload, use the returned document ID and operation ID.

```text
POST /admin/documents/upload
  returns document_id + operation_id + status_url

GET /documents/{document_id}/processing-status
  normal user document status

GET /admin/documents/{document_id}/processing-status
  admin document status

GET /admin/lightrag/domains/{domain_id}/documents/processing-status
  admin domain documents table
```

## Status model

```text
Document status:
  uploaded | indexing | ready | failed | deleted

Operation status:
  queued | running | succeeded | failed | canceled

Operation stage:
  queued
  saving
  parsing
  extracting_assets
  indexing_lightrag
  waiting_remote
  complete
  failed
```

## Raw LightRAG status handling

Remote LightRAG status should be mapped to app-level status inside the backend.

Do not show raw statuses as primary UI states.

Examples:

```text
LightRAG pending/queued       -> operation.status=queued
LightRAG processing/indexing  -> operation.status=running, stage=indexing_lightrag
LightRAG ready/completed      -> operation.status=succeeded, document.status=ready
LightRAG failed/error         -> operation.status=failed, document.status=failed
```
