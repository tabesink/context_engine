# Document Upload Workflow

Document upload is a staged workflow. The route should stay small, while the worker and services own parsing, LightRAG push, and remote polling.

## Contract

`POST /admin/documents/upload` should:

1. Validate the admin request and requested LightRAG domain.
2. Save the uploaded source file.
3. Create the document row.
4. Create the operation row.
5. Enqueue document processing.
6. Return `document_id`, `operation_id`, and `processing_status_url`.

Clients should poll `GET /documents/{document_id}/processing-status` or the admin equivalent. New UI code should not poll `ingestion-status`.

## Stages

Public operation stages are:

- `register_upload`: upload accepted, document and operation registered.
- `parse_local_structure`: source file is being parsed into local pages, sections, blocks, chunks, and assets.
- `push_to_lightrag`: parsed source chunks are being sent to the selected LightRAG domain.
- `poll_remote_indexing`: Context Engine is waiting for LightRAG indexing to finish.
- `complete`: processing finished successfully.
- `failed`: processing failed.

User-facing labels should stay stable and concise:

```text
Queued
Parsing local structure
Sending to LightRAG
Waiting for LightRAG indexing
Ready
Failed
```

## Ownership

- `documents.status` owns current document availability: `uploaded`, `indexing`, `ready`, `failed`, or `deleted`.
- `jobs.status` owns current operation state, exposed through `/operations`.
- `jobs.stage`, `jobs.progress_current`, `jobs.progress_total`, and `jobs.message` own current workflow progress.
- `documents.error_message` and `jobs.error_message` own failure messages at their respective layers.
- `documents.metadata.lightrag` stores remote correlation IDs, provider fingerprints, and diagnostic snapshots only.

Do not make `documents.metadata.lightrag.status` the polling source for new UI.

## Worker Shape

The worker should keep the major steps readable:

```text
document_ingest operation
  -> parse local structure
  -> persist pages/sections/blocks/chunks/assets
  -> push source chunks to LightRAG
  -> poll remote indexing
  -> mark document ready or failed
```

If parsing fails, ingestion fails explicitly instead of raw-uploading the file to LightRAG as a fallback. If LightRAG fails, the document remains locally recorded but unavailable until retry or recovery.
