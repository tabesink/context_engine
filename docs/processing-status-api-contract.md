# Processing Status API Contract

This document defines the normalized response shape used by processing-status surfaces.

## Admin Domain Documents Processing Status

Endpoint:

`GET /admin/lightrag/domains/{domain_id}/documents/processing-status?limit={n}&offset={n}`

Auth:

- Admin only

Purpose:

- Returns paginated per-document status rows for one LightRAG domain.
- Provides page-local status counts and pagination metadata for table UIs.

Response shape:

```json
{
  "domain_id": "default",
  "documents": [
    {
      "document_id": "c8e8d2d0-94f0-4d6d-b4a8-8d8d6b6b2f34",
      "filename": "onboarding.pdf",
      "status": "indexing",
      "domain_id": "default",
      "job_id": "f81f7f6c-64f7-4af2-b91d-8f3a6f78f0df",
      "job_status": "running",
      "lightrag_status": "processing",
      "message": null,
      "can_retry": false,
      "updated_at": "2026-05-28T12:00:00Z"
    }
  ],
  "status_counts": {
    "queued": 0,
    "indexing": 1,
    "ready": 0,
    "failed": 0,
    "deleted": 0,
    "unknown": 0
  },
  "pagination": {
    "limit": 25,
    "offset": 0,
    "returned": 1,
    "total": 14
  },
  "updated_at": "2026-05-28T12:00:01Z"
}
```

Field notes:

- `status_counts` is computed from the returned page (`documents`), not the full domain corpus.
- `pagination.total` is the total document count for the domain before paging.
- `pagination.returned` is the number of rows in this response page.
- `updated_at` is the response generation timestamp from Context Engine.
