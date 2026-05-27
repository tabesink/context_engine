# 01 — Target Architecture

## Permanent goal

LightRAG domain lifecycle owns all runtime prerequisites.

When admin starts or repairs a domain:

```text
Admin API
  -> LightRAGDomainService.repair(domain_id)
  -> PostgresProvisioner.ensure_for_domain(domain)
  -> write_domain_env(domain)
  -> ComposeGenerator.write(domains)
  -> Docker Compose recreate/up
  -> HealthProbe.check(domain runtime URL)
  -> update manifest status
```

## Storage modes

### Mode 1 — `per_domain` recommended

Each managed LightRAG domain gets isolated Postgres objects:

```text
domain_id: fatigue
database:  lightrag_fatigue
role:      lightrag_fatigue
workspace: fatigue
```

Pros:

- no app DB table mixing
- easy to drop/purge one domain later
- clearer debugging
- safer for multi-user/admin-only write app

### Mode 2 — `compat`

Used only to permanently support existing legacy containers that are hard-coded to:

```env
POSTGRES_DATABASE=lightrag
POSTGRES_USER=lightrag
```

This mode should be explicit, visible in diagnostics, and ideally temporary.

### Mode 3 — `app_database_shared` not recommended

LightRAG uses `context_engine` database/user. Avoid this unless you deliberately want app metadata and LightRAG storage tables mixed.

## New settings

Add to `app/core/config.py` and `app/lightrag_deploy/settings.py`:

```env
LIGHTRAG_STORAGE_BACKEND=postgres
LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain
LIGHTRAG_POSTGRES_COMPAT_ENABLED=true
LIGHTRAG_POSTGRES_COMPAT_DATABASE=lightrag
LIGHTRAG_POSTGRES_COMPAT_USER=lightrag
LIGHTRAG_POSTGRES_COMPAT_PASSWORD=lightrag
LIGHTRAG_POSTGRES_ADMIN_DATABASE=context_engine
LIGHTRAG_POSTGRES_VECTOR_EXTENSION=vector
LIGHTRAG_POSTGRES_AGE_EXTENSION=age
LIGHTRAG_TOKENIZER_OFFLINE=true
LIGHTRAG_TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

Allowed provisioning modes:

```text
per_domain
compat
app_database_shared
```

Default recommendation:

```env
LIGHTRAG_STORAGE_BACKEND=postgres
LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain
LIGHTRAG_POSTGRES_COMPAT_ENABLED=true
```

This means new managed domains use `lightrag_<domain>`, but the system also creates `lightrag/lightrag` compatibility objects for old containers until you delete them.

## New service

Create:

```text
app/lightrag_deploy/postgres_provisioner.py
```

Responsibilities:

- connect to admin/runtime DB as `context_engine`
- create role if missing
- create database if missing
- grant privileges
- create `vector` extension in target DB
- create `age` extension where available
- return diagnostics, do not hide failed extension setup

## New repair endpoint

Add:

```http
POST /admin/lightrag/domains/{domain_id}/repair
```

It should:

1. provision Postgres objects
2. optionally provision legacy compatibility DB/role
3. regenerate `domain.env`
4. regenerate generated compose
5. recreate container
6. health-probe runtime URL
7. return exact diagnostics
