# 03 — API Contract Migration

## Canonical API Contracts

### Document Upload

```text
POST /admin/documents/upload
```

Request:

```text
multipart/form-data
file: UploadFile
lightrag_domain_id: string
```

Response target:

```json
{
  "document": {
    "id": "uuid",
    "filename": "example.pdf",
    "status": "processing",
    "lightrag_domain_id": "fatigue"
  },
  "operation_id": "uuid",
  "processing_status_url": "/documents/{id}/processing-status"
}
```

### Document Processing Status

```text
GET /documents/{document_id}/processing-status
GET /admin/documents/{document_id}/processing-status
```

Response target:

```json
{
  "document_id": "uuid",
  "status": "processing|ready|failed",
  "stage": "register_upload|parse_local_structure|push_to_lightrag|poll_remote_indexing|complete|failed",
  "progress": 0,
  "message": "Human readable status",
  "operation_id": "uuid",
  "error_message": null,
  "updated_at": "iso-datetime"
}
```

Deprecated:

```text
GET /documents/{id}/ingestion-status
GET /admin/documents/{id}/ingestion-status
```

Migration rule:

```text
Deprecated endpoints delegate to processing-status during compatibility window.
No frontend code should call deprecated endpoints.
```

### Retrieval

```text
POST /retrieve
```

Request target:

```json
{
  "query": "string",
  "domain_id": "string",
  "document_ids": ["uuid"],
  "mode": "semantic|hybrid|local_navigation"
}
```

Response target:

```json
{
  "answer": "string or null",
  "evidence": [
    {
      "document_id": "uuid",
      "document_title": "string",
      "source_path": "string",
      "chunk_id": "string",
      "reference_id": "string",
      "page_number": 1,
      "text": "string"
    }
  ],
  "assets": [],
  "metadata": {}
}
```

### Operations

```text
GET /operations
GET /operations/{operation_id}
POST /operations/{operation_id}/retry
```

Response target:

```json
{
  "id": "uuid",
  "type": "document_ingest|domain_create|domain_start|domain_stop|domain_delete",
  "status": "queued|running|waiting_remote|succeeded|failed|cancelled",
  "stage": "string",
  "progress": 0,
  "resource_type": "document|domain|provider",
  "resource_id": "string",
  "resource_label": "string",
  "actor_user_id": "uuid",
  "message": "string",
  "error_message": null,
  "created_at": "iso-datetime",
  "updated_at": "iso-datetime"
}
```

Deprecated or debug-only:

```text
GET /jobs
GET /jobs/{id}
POST /jobs/{id}/retry
```

### Domains

Preferred canonical route family:

```text
GET    /domains
GET    /admin/domains
POST   /admin/domains
GET    /admin/domains/{domain_id}
POST   /admin/domains/{domain_id}/start
POST   /admin/domains/{domain_id}/stop
DELETE /admin/domains/{domain_id}
```

Allowed lifecycle actions:

```text
create
start
stop
delete
```

Do not expose in standard UI:

```text
repair
recreate
regenerate
purge
upload document from domain More menu
view documents from domain More menu
view logs from domain More menu
```

### Provider

Lean target:

```text
GET /admin/provider
POST /admin/provider/test
```

Avoid runtime mutation unless intentionally retained:

```text
PUT /admin/ai-settings/defaults
POST /admin/ai-settings/profiles
PATCH /admin/ai-settings/profiles/{id}
PUT /admin/ai-settings/provider-secrets/{name}
```

If these remain, mark clearly as advanced/admin runtime mode.
