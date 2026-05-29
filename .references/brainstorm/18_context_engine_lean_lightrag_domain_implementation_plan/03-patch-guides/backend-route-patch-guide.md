# Backend Route Patch Guide

## File

```text
app/api/routes/lightrag_admin.py
```

## Remove routes

```python
@router.post("/admin/lightrag/domains/{domain_id}/repair")
@router.post("/admin/lightrag/domains/{domain_id}/recreate")
@router.post("/admin/lightrag/domains/{domain_id}/regenerate")
@router.post("/admin/lightrag/domains/{domain_id}/purge-preview")
@router.delete("/admin/lightrag/domains/{domain_id}/purge")
```

## Remove create auto-start

Delete logic equivalent to:

```python
if request.start:
    result = service.repair(domain.id)
    ...
```

Create route should only call:

```python
domain = service.create_domain(request)
```

## Simplify safe delete

Keep:

```python
DELETE /admin/lightrag/domains/{domain_id}
```

It should call:

```python
service.remove(domain_id, permanent=False)
```

Do not support:

```text
permanent=true
purge confirm_domain_id
```

## Remove unused imports/dependencies

Likely remove:

```python
DomainPurgeService
get_domain_purge_service
LightRAGDomainRepairResult
LightRAGDomainPurgePreview
LightRAGDomainPurgeResult
PermanentDeleteDisabledError
```

Only remove after running import checks.
