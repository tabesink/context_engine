# Environment and Deployment Checklist

_Last verified against the codebase: May 2026._

## Current required backend environment

| Variable | Purpose | Notes |
|---|---|---|
| `APP_NAME` | App display/name | Low risk |
| `ENVIRONMENT` | Runtime mode | Use `production` or `local_server` for deployed local network |
| `SECRET_KEY` | Auth token signing | Must be strong; do not keep example |
| `ACCESS_TOKEN_MINUTES` | Auth token lifetime | Choose reasonable value for local operators |
| `POSTGRES_DB` | Backend DB name | Used by compose postgres |
| `POSTGRES_USER` | Backend DB user | Used by compose postgres |
| `POSTGRES_PASSWORD` | Backend DB password | Must change from example |
| `DATABASE_URL` | SQLAlchemy backend DB URL | `.env.example` uses Postgres; `Settings` default is SQLite for local dev |
| `REDIS_URL` | Redis/RQ backend job queue URL | Must point to Redis service |
| `INDEX_JOBS_INLINE` | Inline vs background indexing | Use `false` for concurrent use |
| `STORAGE_ROOT` | Raw backend upload storage | Persistent path, default `.data/uploads` |
| `API_PORT` | Published backend API port | Avoid conflicts |
| `PUBLISH_POSTGRES_PORT` | Host Postgres port | Optional host publish for dev/admin tools |
| `PUBLISH_REDIS_PORT` | Host Redis port | Optional host publish for dev/admin tools |
| `ALLOWED_ORIGINS` | CORS | Do not leave `*` for broader deployment |
| `SEED_ADMIN_EMAIL` | Seed admin | Change for deployment |
| `SEED_ADMIN_PASSWORD` | Seed password | Strong password |

## LightRAG runtime integration (current)

| Variable | Purpose | Code default | `.env.example` |
|---|---|---|---|
| `LIGHTRAG_ENABLED` | Remote upload/retrieval/graph | `false` | `true` (dev convenience) |
| `LIGHTRAG_BASE_URL` | Single remote LightRAG URL | `http://localhost:9621` | same |
| `LIGHTRAG_API_KEY` | Bearer token | empty | empty |
| `LIGHTRAG_DOMAIN` | Default domain name | `default` | `default` |
| `LIGHTRAG_DOMAIN_MANIFEST` | Domain manifest path | `.data/lightrag/domains.json` | same |
| `LIGHTRAG_TIMEOUT_SECONDS` | Remote HTTP timeout | `10` | `10` |

## LightRAG domain deployment control (current)

Defined in `app/core/config.py` and `.env.example`. Mutating admin domain APIs return HTTP 400 until `LIGHTRAG_DEPLOY_ENABLED=true`.

| Variable | Purpose | Code default |
|---|---|---|
| `LIGHTRAG_DEPLOY_ENABLED` | Gate admin domain CRUD/up/down | `false` |
| `LIGHTRAG_DEPLOY_ROOT` | Deploy artifact root | `.data/lightrag` |
| `LIGHTRAG_DOMAINS_ROOT` | Per-domain folders | `.data/lightrag/domains` |
| `LIGHTRAG_DOMAINS_MANIFEST` | Manifest path (usually same as `LIGHTRAG_DOMAIN_MANIFEST`) | `.data/lightrag/domains.json` |
| `LIGHTRAG_COMPOSE_FILE` | Generated compose file | `.data/lightrag/docker-compose.lightrag-domains.yml` |
| `LIGHTRAG_DELETED_ROOT` | Archived domains | `.data/lightrag/deleted` |
| `LIGHTRAG_DEFAULT_PORT_START` | Host port allocation | `9621` |
| `LIGHTRAG_DEFAULT_CONTAINER_PORT` | Container listen port | `9621` |
| `LIGHTRAG_DOCKER_NETWORK` | Docker network name | `context_engine_lightrag` |
| `LIGHTRAG_DOMAIN_ENV_FILENAME` | Per-domain env file name | `domain.env` |
| `LIGHTRAG_IMAGE` | LightRAG container image | `ghcr.io/hkuds/lightrag:latest` |
| `LIGHTRAG_DOCKER_EXECUTION_MODE` | Compose runner mode | `host` |
| `LIGHTRAG_DOCKER_COMPOSE_BIN` | Compose binary | `docker compose` |
| `LIGHTRAG_DOCKER_TIMEOUT_SECONDS` | Compose command timeout | `120` |

Optional (only if configuring LightRAG external storage): `LIGHTRAG_POSTGRES_URL`, `LIGHTRAG_REDIS_URL`, `LIGHTRAG_NEO4J_*`, `LIGHTRAG_ARCHIVE_DELETED_DOMAINS`, `LIGHTRAG_ALLOW_PERMANENT_DELETE`.

## Deployment checklist for Option 1

```text
[ ] Configure backend `.env` with strong secrets.
[ ] Start backend postgres/redis/api/worker.
[ ] Confirm `/health` passes.
[ ] Confirm admin login works.
[x] LightRAG deployment settings exist in config and `.env.example`.
[ ] Set LIGHTRAG_DEPLOY_ENABLED=true for domain management.
[ ] Create first LightRAG domain through admin route/TUI.
[ ] Confirm `.data/lightrag/domains/<domain_id>/` exists.
[ ] Confirm domain env file exists.
[ ] Confirm generated compose file exists.
[ ] Start domain container (up).
[ ] Confirm domain base URL is reachable.
[ ] Confirm manifest contains domain.
[ ] Set LIGHTRAG_ENABLED=true after domain is healthy.
[ ] Upload document via POST /admin/documents/upload with lightrag_domain_id.
[ ] Confirm local document row stores track_id.
[ ] Poll/refresh status until READY (not automated yet — implement or manual).
[ ] Query domain as normal user with lightrag_domain_id.
[ ] Run two simultaneous query requests.
[ ] Upload while querying and verify reads remain available.
```

## Backup checklist

```text
[ ] Dump backend PostgreSQL database.
[ ] Copy `.data/uploads`.
[ ] Copy `.data/lightrag`.
[ ] Save `.env` securely outside normal repo.
[ ] Document exact app version and generated compose file.
```

## What not to do yet

```text
[ ] Do not add separate Postgres/Redis for LightRAG unless proven required (Option 3+).
[ ] Do not let operators manually edit generated domain compose files.
[ ] Do not allow two same-domain ingestion jobs at once until ingest lock is implemented.
[ ] Do not rely on LIGHTRAG_ENABLED alone to decide every upload target (add explicit engine field).
```
