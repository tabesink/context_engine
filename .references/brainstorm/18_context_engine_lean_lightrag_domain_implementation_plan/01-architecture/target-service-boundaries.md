# Target Service Boundaries

## Public `LightRAGDomainService` methods

Keep public methods aligned with product/API concepts:

```python
list_domains()
get_domain(domain_id)
create_domain(request)
up(domain_id)
down(domain_id)
remove(domain_id, permanent=False)
```

Remove or privatize:

```python
repair(domain_id)
recreate(domain_id)
regenerate(domain_id=None)
```

## Private helper boundaries

Private helpers can stay technical:

```python
_prepare_runtime_artifacts(domain)
_resolve_runtime_config(domain)
_ensure_postgres_identity(domain)
_provision_domain_postgres(domain)
_write_domain_env(domain, runtime_config)
_write_compose()
_probe_health(domain)
_persist_status(domain, status, message=None)
```

## Important rule

Do not delete useful technical logic. Move it behind Start.

```text
Public route removed does not mean useful implementation logic is deleted.
```

Example:

```text
regenerate route removed
  -> artifact regeneration logic remains inside Start
```
