# API Contract Plan

## Goal

Let the UI poll one operation model for all long-running work while keeping old job endpoints stable during transition.

## Operation response shape

```json
{
  "id": "uuid",
  "operation_type": "document_ingest",
  "status": "running",
  "resource_type": "document",
  "resource_id": "document_uuid",
  "requested_by_user_id": "user_uuid",
  "progress_current": 3,
  "progress_total": 10,
  "error_message": null,
  "metadata": {},
  "created_at": "2026-05-29T00:00:00Z",
  "started_at": "2026-05-29T00:00:05Z",
  "finished_at": null,
  "updated_at": "2026-05-29T00:00:10Z"
}
```

## Endpoint plan

Add:

```text
GET /api/operations
GET /api/operations/{operation_id}
```

Optional filters:

```text
?resource_type=document
?resource_id=<id>
?status=running
?limit=50
```

Keep temporarily:

```text
GET /api/jobs
GET /api/jobs/{job_id}
```

Implementation options:

```text
Option A: /api/jobs calls the same service as /api/operations.
Option B: /api/jobs returns operation rows but keeps old field aliases.
```

## Domain lifecycle API plan

Lean public/admin API:

```text
POST /api/admin/lightrag-domains
POST /api/admin/lightrag-domains/{domain_id}/start
POST /api/admin/lightrag-domains/{domain_id}/stop
DELETE /api/admin/lightrag-domains/{domain_id}
GET /api/lightrag-domains
GET /api/admin/lightrag-domains/{domain_id}
```

Remove from normal UI exposure:

```text
repair
recreate
regenerate
purge
```

Backend can keep emergency scripts or internal admin-only utilities, but do not make these first-class UI lifecycle actions.

## Document API plan

Documents should remain the place for:

```text
upload document
view documents
document processing status
```

Do not expose upload/view documents inside the domain card More menu.

## Domain card UI behavior

Normal domain card actions:

```text
Start
Stop
Delete
```

No:

```text
Upload Documents
View Documents
View Logs
Repair
Recreate
Regenerate
Purge
```

Logs/status should live in Jobs / Operations / Audit surfaces.
