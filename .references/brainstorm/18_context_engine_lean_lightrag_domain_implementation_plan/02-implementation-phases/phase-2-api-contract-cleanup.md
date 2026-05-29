# Phase 2 — API Contract Cleanup

## Goal

Make the frontend/backend API contract match the lean product model.

## Backend route cleanup

Remove routes from `app/api/routes/lightrag_admin.py`:

```text
POST /admin/lightrag/domains/{domain_id}/repair
POST /admin/lightrag/domains/{domain_id}/recreate
POST /admin/lightrag/domains/{domain_id}/regenerate
POST /admin/lightrag/domains/{domain_id}/purge-preview
DELETE /admin/lightrag/domains/{domain_id}/purge
```

## Create request cleanup

Remove from `LightRAGDomainCreateRequest`:

```text
start
top_k
chunk_top_k
chunk_rerank_top_k
max_token_for_text_unit
max_token_for_global_context
max_token_for_local_context
```

## Route behavior cleanup

Remove create auto-start block:

```python
if request.start:
    result = service.repair(domain.id)
```

## Frontend API client cleanup

Remove API methods:

```text
repair
recreate
regenerate
purgePreview
purge
```

Keep:

```text
list
create
up
down
remove/deleteDomain
```

## Compatibility choice

For an internal app, delete routes now.

For deployed clients, return `410 Gone` for one release:

```json
{
  "detail": "This operation was removed. Use Start, Stop, or Delete."
}
```

## Acceptance criteria

- OpenAPI no longer lists removed routes.
- Frontend does not call removed routes.
- Create request schema is small.
- Backend rejects unexpected fields if strict request validation is enabled.
