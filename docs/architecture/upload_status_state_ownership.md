# Upload Status State Ownership

## Core Rule

Upload creates a document and one operation. The operation owns active progress, the
document owns current availability, and processing-status endpoints are the normal UI
polling surface.

## Owners

- `documents.status` owns whether the document is currently usable: `uploaded`,
  `indexing`, `ready`, `failed`, or `deleted`.
- `jobs.status` owns active operation state. The table name remains `jobs`,
  but the product/API concept is `operations`:
  `queued`, `running`, `succeeded`, `failed`, or `canceled`.
- `jobs.stage` owns the current processing phase, using public stage names:
  `register_upload`, `parse_local_structure`, `push_to_lightrag`,
  `poll_remote_indexing`, `complete`, or `failed`.
- `jobs.message` owns the short user-facing progress message.
- `documents.error_message` owns the current document-level failure reason.
- `jobs.error_message` owns the operation-level failure reason.
- `documents.metadata.lightrag` owns remote identifiers, embedding fingerprints,
  and diagnostic remote status snapshots only.

## Endpoint Roles

- `POST /admin/documents/upload` creates the document and operation.
- `GET /documents/{document_id}/processing-status` is the normal user polling
  endpoint.
- `GET /admin/documents/{document_id}/processing-status` is the admin equivalent
  for a single document.
- `GET /admin/lightrag/domains/{domain_id}/documents/processing-status` is the
  admin domain document status list.
- `GET /admin/lightrag/domains/{domain_id}/processing-status` summarizes domain
  processing activity.
- `GET /operations` and `GET /operations/{operation_id}` are the admin async
  visibility endpoints.
- `POST /operations/{operation_id}/retry` retries retryable document ingest
  operations.
- `POST /admin/documents/{document_id}/refresh-status` is manual recovery only.
- `POST /admin/documents/{document_id}/retry-ingestion` is the product-facing
  retry action.

## LightRAG Metadata

LightRAG metadata is diagnostic, not authoritative app state. Keep remote
correlation and diagnostic fields there:

```json
{
  "lightrag": {
    "domain_id": "fatigue",
    "embedding_profile_id": "openai-text-embedding-3-small",
    "embedding_fingerprint": "...",
    "document_id": "remote-doc",
    "track_id": "track-123",
    "last_remote_status": "processing",
    "last_remote_check_at": "2026-05-29T12:00:00Z"
  }
}
```

Do not use `metadata.lightrag.status` as the UI source of truth for new code.

## Allowed Transitions

Document transitions:

```text
uploaded -> indexing -> ready
uploaded -> indexing -> failed
failed   -> indexing -> ready
failed   -> indexing -> failed
any      -> deleted
```

Operation transitions:

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> canceled
running -> canceled
```

Stage values stay scalar and intentionally simple. Do not add an upload-stage
event table until the product needs history rather than current progress.
