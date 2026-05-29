# Phase 3 — Service Consolidation

## Goal

Make Start the only boot/recovery operation.

## File likely affected

```text
app/lightrag_deploy/service.py
```

## Public service methods after refactor

```python
list_domains()
get_domain(domain_id)
create_domain(request)
up(domain_id)
down(domain_id)
remove(domain_id, permanent=False)
```

## Remove or privatize

```python
repair(domain_id)
recreate(domain_id)
regenerate(domain_id=None)
```

## Consolidate behavior into `up()`

`up()` should do:

```text
load domain
prepare runtime artifacts
write domain.env
write compose
provision Postgres if needed
Docker build/up
health probe
persist status
return operation result
```

## Do not lose useful internals

If `repair()` currently has better health/provisioning diagnostics, preserve diagnostics in logs or internal helper results.

If `regenerate()` currently rewrites env/Compose, keep that logic inside `_prepare_runtime_artifacts()`.

If `recreate()` currently force recreates, decide whether `up()` needs force behavior. Prefer normal `docker compose up -d` unless tests prove force-recreate is required.

## Acceptance criteria

- No route can call repair/recreate/regenerate.
- Start handles runtime artifact refresh.
- Start works after provider API key changes.
- Start works after generated Compose is stale/missing.
- Unit tests cover Start as canonical boot path.
