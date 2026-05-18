# 5. Domain Lifecycle and Document Flow

## 5.1 Domain Lifecycle

### Create domain

```text
Admin TUI
  ↓
POST /admin/lightrag/domains
  ↓
LightRAGDomainService.create_domain()
  ↓
validate domain ID
  ↓
choose/validate host port
  ↓
create .data/lightrag/domains/<domain>/ folders
  ↓
generate domain.env
  ↓
update .data/lightrag/domains.json
  ↓
regenerate .data/lightrag/docker-compose.lightrag-domains.yml
  ↓
audit log
  ↓
return domain response
```

### Start domain

```text
POST /admin/lightrag/domains/{domain_id}/up
  ↓
load manifest
  ↓
ensure compose is up to date
  ↓
docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml up -d lightrag_<domain>
  ↓
poll health endpoint
  ↓
audit log
  ↓
return operation result
```

### Stop domain

```text
POST /admin/lightrag/domains/{domain_id}/down
  ↓
docker compose -f ... stop lightrag_<domain>
  ↓
audit log
  ↓
return operation result
```

### Recreate domain

```text
POST /admin/lightrag/domains/{domain_id}/recreate
  ↓
docker compose -f ... up -d --force-recreate lightrag_<domain>
  ↓
poll health
  ↓
audit log
  ↓
return operation result
```

### Archive/remove domain

```text
DELETE /admin/lightrag/domains/{domain_id}
  ↓
stop container if running
  ↓
remove from manifest
  ↓
regenerate compose
  ↓
move .data/lightrag/domains/<domain>/ to .data/lightrag/deleted/<domain>-timestamp/
  ↓
audit log
  ↓
return archive path
```

### Permanent delete

```text
DELETE /admin/lightrag/domains/{domain_id}?permanent=true
```

Allowed only if:

```env
LIGHTRAG_ALLOW_PERMANENT_DELETE=true
```

and the API request explicitly asks for permanent delete.

## 5.2 Domain States

Use simple states:

```text
configured      # manifest/folders/env exist; not necessarily running
starting        # operation in progress if tracked
running         # container appears running and health OK
stopped         # container stopped
unhealthy       # container running but health check fails
archived        # removed from active manifest and moved to deleted/
error           # last operation failed
```

Do not overbuild state machines in v1. Most status can be computed from manifest + Docker status + health check.

## 5.3 One Document Belongs to One Domain

Rule:

```text
A document uploaded to LightRAG domain `fatigue` belongs only to `fatigue`.
```

Do not fan out one document to multiple LightRAG domains in v1.

## 5.4 Upload Flow With Domain Selection

```text
Admin selects domain in TUI upload screen
  ↓
POST /admin/documents/upload with domain_id=fatigue
  ↓
DocumentService saves local mirror file under Context Engine storage
  ↓
Document row records lightrag_domain_id=fatigue
  ↓
DocumentService resolves domain base_url from manifest
  ↓
LightRAGRemoteAdapter.for_domain(fatigue).upload_document(...)
  ↓
Document row stores external document ID / track ID / status
  ↓
return document response
```

## 5.5 Query Flow With Domain Selection

Normal user query:

```text
User selects domain: fatigue
  ↓
POST /query/retrieve or /query/answer with lightrag_domain_id=fatigue
  ↓
RetrievalService validates domain exists and user can read
  ↓
RetrievalRoutingPolicy selects LightRAG for semantic/hybrid/auto if enabled
  ↓
LightRAGRemoteAdapter uses domain-specific base_url/api_key
  ↓
Evidence normalized into Context Engine response
```

## 5.6 Suggested Query Request Extension

Add optional domain field:

```python
class QueryRequest(BaseModel):
    query: str
    mode: RetrievalMode = RetrievalMode.AUTO
    document_ids: list[UUID] | None = None
    lightrag_domain_id: str | None = None
    top_k: int = 8
    include_debug: bool = False
```

Rules:

- If `lightrag_domain_id` is omitted, use default domain.
- If `mode=navigation`, local Context Engine navigation path may ignore LightRAG domain unless document filtering requires it.
- If `document_ids` are provided, ensure those documents belong to the selected domain or return `400`.

## 5.7 Suggested Upload Request Extension

Admin upload should accept domain ID:

```text
POST /admin/documents/upload
multipart/form-data:
  file=<file>
  lightrag_domain_id=fatigue
```

Rules:

- `lightrag_domain_id` is required when `LIGHTRAG_ENABLED=true` and multiple domains exist.
- If omitted and only one/default domain exists, use default.
- If domain is stopped/unhealthy, return clear error before uploading.

## 5.8 Document Metadata

At minimum store in document metadata:

```json
{
  "lightrag": {
    "domain_id": "fatigue",
    "external_document_id": "external-doc-id",
    "track_id": "upload-track-id",
    "status": "indexing",
    "base_url_key": "fatigue"
  }
}
```

If you already have DB columns for external engine/status, prefer columns for frequently queried fields and metadata for provider-specific payload.

## 5.9 Deleting Documents

Document delete should be separate from domain delete.

V1 recommendation:

- Context Engine marks document deleted locally.
- If LightRAG delete-document API is stable, optionally forward delete to selected domain.
- If LightRAG delete API is not stable, document remains in LightRAG until domain rebuild/reindex.
- Document should be hidden from Context Engine query results once local status is deleted.

## 5.10 Status Polling

Use existing LightRAG track status helper if present.

Add later if not already exposed:

```text
POST /admin/documents/{document_id}/refresh-lightrag-status
```

This is lower priority than domain create/list/up/down.
