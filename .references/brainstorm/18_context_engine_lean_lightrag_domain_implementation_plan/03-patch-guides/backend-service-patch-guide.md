# Backend Service Patch Guide

## File

```text
app/lightrag_deploy/service.py
```

## Keep public API

```python
class LightRAGDomainService:
    def list_domains(...): ...
    def get_domain(...): ...
    def create_domain(...): ...
    def up(...): ...
    def down(...): ...
    def remove(...): ...
```

## Remove public methods

```python
repair()
recreate()
regenerate()
```

If helper logic is needed, move it behind private methods.

## Target `create_domain()`

Create should:

```text
validate domain
allocate port
resolve embedding profile
store embedding snapshot
create folders
write manifest
write initial env/compose if needed
set status configured/stopped
```

Create should not:

```text
call repair
call up
call Docker
probe health
```

## Target `up()`

Start should:

```text
load domain
resolve runtime config
write domain.env
write Compose
provision Postgres
Docker build/up
probe health
persist status
```

## Target `remove()`

Delete should:

```text
remove from manifest
rewrite Compose
move runtime folder to deleted/archive area
preserve documents/jobs/assets
```

## Deletion of purge service

After routes are removed and tests pass, remove `DomainPurgeService` only if no imports remain.
