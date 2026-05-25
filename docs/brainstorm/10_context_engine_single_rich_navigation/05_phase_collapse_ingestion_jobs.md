# 05 — Phase: Collapse Ingestion Jobs

## Goal

Replace multiple overlapping job kinds with one clear ingestion job.

## Current Entropy

Current job kinds may include:

```text
index_document
navigation_process_document
lightrag_ingest_document
```

This reflects the old split:

```text
old local navigation job
new/rich processing job
remote LightRAG ingestion job
```

## Target

One job kind:

```text
document_ingest
```

Meaning:

```text
document_ingest
  ├── parse rich DocumentStructure
  ├── persist pages/sections/blocks/source_chunks/assets
  ├── send source_chunks to LightRAG
  └── update document status
```

## Files to Inspect/Change

```text
app/services/job_service.py
app/workers/tasks.py
app/services/indexing_service.py
app/services/lightrag_ingestion_service.py
app/api/routes/jobs.py
app/api/routes/admin.py
tests/jobs/...
tests/workers/...
```

## Remove/Retire

```text
enqueue_index_document()
enqueue_navigation_process_document()
run_index_job()
run_navigation_process_job()
IndexingService
NavigationIndexBuilder
old DocumentParser path
```

## Keep

```text
enqueue_document_ingest()
run_document_ingest_job()
LightRAGIngestionService.ingest_document()
```

Rename if needed:

```text
LightRAGIngestionService
```

could eventually become:

```text
DocumentIngestionService
```

because it now does both local rich structure persistence and LightRAG ingestion.

## Job Retry Fix

Current anti-pattern:

```text
POST /jobs/{id}/retry
  always calls run_index_job()
```

Target:

```text
POST /jobs/{id}/retry
  if kind == document_ingest:
      run_document_ingest_job()
  else:
      400 unsupported job kind
```

If all jobs are collapsed, retry becomes simple.

## Tests

```text
[ ] Upload enqueues document_ingest.
[ ] Worker runs document_ingest.
[ ] Retry reruns document_ingest.
[ ] Old job kinds cannot be created.
[ ] Old job runner methods are removed.
```

## Acceptance Criteria

```text
[ ] There is one document ingestion job kind.
[ ] Jobs no longer encode old navigation vs LightRAG split.
[ ] Retry behavior is correct.
```
