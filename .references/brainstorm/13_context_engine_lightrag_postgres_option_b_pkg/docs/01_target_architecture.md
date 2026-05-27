# 01 — Target Architecture: Option B

## Goal

Implement Postgres-backed LightRAG domain storage cleanly and explicitly.

## Target storage boundary

```text
Context Engine Postgres database
├── users
├── auth/session metadata
├── app documents table
├── jobs
├── audit logs
└── domain registry/lifecycle metadata

LightRAG domain Postgres databases
├── lightrag_fatigue
│   ├── LightRAG KV/doc status tables
│   ├── LightRAG vector tables
│   └── LightRAG AGE graph data
└── lightrag_other_domain
    ├── LightRAG KV/doc status tables
    ├── LightRAG vector tables
    └── LightRAG AGE graph data
```

## Recommended mode

Use **per-domain database + per-domain role**.

For a domain named `fatigue`:

```text
database: lightrag_fatigue
user:     lightrag_fatigue
password: value from LIGHTRAG_POSTGRES_PASSWORD
host:     postgres
port:     5432
```

This is cleaner than putting LightRAG tables inside the app database.

## New explicit settings

Add these settings to `app/core/config.py` and `app/lightrag_deploy/settings.py`:

```env
LIGHTRAG_STORAGE_BACKEND=postgres
LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain
LIGHTRAG_POSTGRES_HOST=postgres
LIGHTRAG_POSTGRES_PORT=5432
LIGHTRAG_POSTGRES_DATABASE_PREFIX=lightrag
LIGHTRAG_POSTGRES_USER_PREFIX=lightrag
LIGHTRAG_POSTGRES_PASSWORD=lightrag
LIGHTRAG_POSTGRES_VECTOR_INDEX_TYPE=HNSW
```

Supported values:

```text
LIGHTRAG_STORAGE_BACKEND:
  postgres
  file       # optional escape hatch, not the chosen implementation path

LIGHTRAG_POSTGRES_PROVISIONING_MODE:
  per_domain
  shared_runtime  # optional fallback, not recommended as default
```

## Domain lifecycle

### Create domain

```text
POST /admin/lightrag/domains
  -> validate domain id
  -> create manifest object with domain postgres_database/postgres_user
  -> provision Postgres role/database/extensions
  -> write domain.env
  -> write generated compose
  -> save manifest
```

### Regenerate domain

```text
POST /admin/lightrag/domains/{domain_id}/regenerate
  -> load domain
  -> provision Postgres idempotently
  -> rewrite domain.env using domain-level DB values
  -> rewrite generated compose
```

### Repair domain

```text
POST /admin/lightrag/domains/{domain_id}/repair
  -> load domain
  -> normalize missing postgres fields if needed
  -> provision Postgres role/database/extensions
  -> regenerate domain.env and compose
  -> recreate/start the LightRAG container
  -> run health check
  -> return diagnostics
```

## Generated `domain.env` target

For `fatigue`, generated env should contain:

```env
WORKSPACE=fatigue
HOST=0.0.0.0
PORT=9621
INPUT_DIR=/app/data/inputs
WORKING_DIR=/app/data/rag_storage
LOG_DIR=/app/data/logs

LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage
LIGHTRAG_GRAPH_STORAGE=PGGraphStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
POSTGRES_PASSWORD=${LIGHTRAG_POSTGRES_PASSWORD value}
POSTGRES_VECTOR_INDEX_TYPE=HNSW
```

It should not say `POSTGRES_USER=lightrag` unless the role `lightrag` is intentionally provisioned.

