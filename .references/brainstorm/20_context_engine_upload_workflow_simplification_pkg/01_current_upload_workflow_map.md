# Current Upload Workflow Map

## Current conceptual flow

```text
Admin uploads file
   │
   ▼
POST /admin/documents/upload
   │
   ▼
DocumentService.upload()
   │
   ├─ validate domain
   ├─ validate provider/model readiness
   ├─ validate LightRAG reachability
   ├─ save file
   ├─ create documents row
   │    documents.status = indexing
   │    metadata.lightrag.status = queued
   │
   └─ enqueue document_ingest job
        jobs.status = queued
   │
   ▼
Worker
   │
   ├─ job.status = running
   ├─ parse document
   ├─ save local structure/assets
   ├─ push chunks to LightRAG
   └─ job.status = succeeded / failed
   │
   ▼
Status poller
   │
   └─ refresh pending LightRAG statuses
```

## Current endpoint families

### Upload / admin document actions

```text
POST /admin/documents/upload
POST /admin/documents/{document_id}/reingest
POST /admin/documents/{document_id}/refresh-status
```

### Narrow ingestion status

```text
GET /documents/{document_id}/ingestion-status
GET /admin/documents/{document_id}/ingestion-status
```

### Rich processing status

```text
GET /documents/{document_id}/processing-status
GET /admin/documents/{document_id}/processing-status
GET /lightrag/domains/{domain_id}/processing-status
GET /admin/lightrag/domains/{domain_id}/processing-status
GET /admin/lightrag/domains/{domain_id}/documents/processing-status
```

### Raw jobs/admin diagnostics

```text
GET /jobs
GET /jobs/{job_id}
POST /jobs/{job_id}/retry
```

## Current complexity

```text
Problem 1:
  UI can choose between ingestion-status, processing-status, and jobs.

Problem 2:
  document metadata may carry LightRAG status while jobs also carry status.

Problem 3:
  retry can be document-based or job-based.

Problem 4:
  manual refresh and backend poller overlap conceptually.

Problem 5:
  LightRAG raw status leaks into product-level status language.
```
