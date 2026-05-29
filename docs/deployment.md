# Deployment Notes

The supported local deployment uses Docker Compose with PostgreSQL, Redis, the API, one ingestion worker, and one LightRAG status poller. This is the canonical startup topology for queue-backed indexing. Context Engine can also manage same-machine LightRAG domain containers through admin-only deployment-control APIs; generated LightRAG services share the same Docker network and use per-domain PostgreSQL databases.

## Required Environment

Copy `.env.example` and change production-sensitive values before running outside local development.

```bash
cp .env.example .env
```

Append optional overlays only when needed:

```bash
# Enable admin-managed LightRAG domain lifecycle:
cat .env.lightrag-deploy.example >> .env

# Include provider settings written into generated domain.env files:
cat .env.lightrag-provider.example >> .env
```

Important settings:

- `SECRET_KEY`: strong random value; never use the development default in production.
- `PUBLISH_POSTGRES_PORT`, `PUBLISH_REDIS_PORT`, `API_PORT`: host port mappings exposed by Compose. `.env.example` is host-first and maps PostgreSQL to `5438`, Redis to `6386`, and the API to `8010`.
- `DATABASE_URL`: required SQLAlchemy URL. PostgreSQL is the only supported runtime database for local development, staging, and production. Compose injects the in-network value `postgresql+psycopg://context_engine:context_engine@postgres:5432/context_engine` into containers.
- `REDIS_URL`: Redis URL. `.env.example` uses the host URL; Compose injects `redis://redis:6379/0` into API/worker containers.
- `CONTEXT_ENGINE_API_BASE_URL` (optional): default base URL the `context-engine` terminal client uses when `--api-base-url` is omitted. Keep this aligned with `API_PORT`.
- `NEXT_PUBLIC_BACKEND_BASE_URL` (optional): frontend base URL for browser calls. Set this to the same backend origin (for example `http://127.0.0.1:8010`) when running the web client.
- `INDEX_JOBS_INLINE`: `false` for worker-backed indexing; `true` only for deterministic local tests/dev flows.
- `LIGHTRAG_STATUS_POLL_INTERVAL_SECONDS`: interval for background LightRAG status synchronization.
- `STORAGE_ROOT`: persistent mounted upload directory.
- `SEED_ADMIN_USERNAME` and `SEED_ADMIN_PASSWORD`: first admin credentials for `scripts.seed_admin`.
- `ALLOWED_ORIGINS`: comma-separated CORS origins, or `*` for local development.
- `LIGHTRAG_DOMAIN_REGISTRY`: required LightRAG domain registry path. Every upload, retrieve, graph, and workspace-tree request must target a domain registered in this file.
- `LIGHTRAG_TIMEOUT_SECONDS`: HTTP timeout for LightRAG calls.
- `QUERY_LOG_STORE_TEXT` and `QUERY_LOG_RETENTION_DAYS`: query log text persistence and retention controls.
- `LIGHTRAG_DEPLOY_ENABLED`: gates **mutating** LightRAG domain deployment APIs (`/admin/lightrag-domains...`). The read-only `GET /lightrag/domains` listing remains available to authenticated users so clients can choose `lightrag_domain_id` when manifests exist. Use `.env.lightrag-deploy.example` only when Context Engine manages LightRAG containers.
- LightRAG provider settings (`LIGHTRAG_LLM_*`, `LIGHTRAG_EMBEDDING_*`) live in `.env.lightrag-provider.example` because they are written into generated LightRAG domain env files, not needed for fixed external LightRAG retrieval.

In `app/core/config.py`, LightRAG runtime resolution uses only the domain registry. `lightrag_deploy_enabled` remains `false` by default so domain lifecycle control stays opt-in.

## First Run With Compose

For containerized API/worker runs, make sure `.env` uses service names for internal URLs:

```env
DATABASE_URL=postgresql+psycopg://context_engine:context_engine@postgres:5432/context_engine
REDIS_URL=redis://redis:6379/0
INDEX_JOBS_INLINE=false
```

Then start the stack and seed admin (adjust service name if your compose file differs):

```bash
docker compose up --build
docker compose exec api python -m scripts.seed_admin
```

Alternatively, `docker compose run --rm api python -m scripts.seed_admin` works before the stack is fully up; use whichever fits your workflow.

The `worker` service must stay up when `INDEX_JOBS_INLINE=false`. It consumes indexing jobs and moves them through `queued`, `running`, `succeeded`, or `failed`.
The `status-poller` service should also stay up in that mode so documents that remain `indexing` in LightRAG can transition to `ready`/`failed` without manual refresh calls.
`scripts/deploy-all.sh` (and PowerShell variant) now use this Compose backend path by default.

For bind mounts and API reload during local development, layer the dev override on top:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Database Migrations

Schema changes are managed with Alembic. Existing local development still creates missing tables on startup for convenience, but durable feature work should add an Alembic revision.

```bash
alembic upgrade head
```

The baseline revision records the schema that existed before document-structure and asset tables were introduced.

## Published Ports And `.env.example`

Compose maps **host** ports from your `.env` (`PUBLISH_POSTGRES_PORT`, `PUBLISH_REDIS_PORT`, `API_PORT`). The checked-in `.env.example` publishes PostgreSQL and Redis on alternate localhost ports while keeping the API on `8010`. Set `DATABASE_URL` and `REDIS_URL` to those same localhost ports when you run tooling on the host; services **inside** the Compose network use hostnames `postgres` and `redis` with container ports `5432` and `6379`.

## Local Non-Compose Run

For a quick local API run, install the package and run Uvicorn from the repository root:

```bash
python -m pip install -e ".[dev]"
uvicorn app.main:create_app --factory --reload --port 8010
```

`DATABASE_URL` must be configured. Local non-compose runs should point at the PostgreSQL service started above; the app no longer falls back to a hidden sqlite file database.
When `INDEX_JOBS_INLINE=false`, local non-compose mode requires manual worker and status poller terminals, or uploads can remain queued/indexing.

## Terminal Client (Deprecated)

The terminal client/TUI is deprecated and is not part of the supported deployment surface.

- Prefer direct HTTP API usage and supported web/admin interfaces.
- Legacy CLI/TUI code may still exist in-repo for transition purposes, but it should be treated as unsupported.

## Auth Contract (Frozen)

The backend auth API contract is intentionally fixed:

- `POST /auth/login` with body `{ "username": string, "password": string }`
- Response `{ "access_token": string, "token_type": "bearer" }`
- `GET /auth/me` requires `Authorization: Bearer <access_token>`

No `/api/v1/auth/*` compatibility aliases are provided. Clients should configure API base URLs and endpoint maps to call `/auth/*` directly.

## LightRAG Runtime

LightRAG is the semantic retrieval runtime:

```env
LIGHTRAG_DOMAIN_REGISTRY=.data/lightrag/domains.json
```

- `auto`, `semantic`, and `hybrid` query modes use remote LightRAG.
- Requests must include `lightrag_domain_id`; Context Engine rejects unknown domains before proxying to LightRAG.
- `hybrid` may add local navigation evidence when available.
- `navigation` query mode remains local page/tree retrieval.
- Admin uploads enqueue `document_ingest`; the worker builds canonical structure/source chunks, ingests chunks to LightRAG, polls status, and updates `documents.metadata.lightrag`.
- Admin/WebUI status flow should poll `GET /jobs/{job_id}` and `GET /admin/documents/{document_id}/ingestion-status` until document status reaches a terminal state.
- Structure-processing failures fail ingestion explicitly (no raw LightRAG upload fallback).
- Unknown upstream LightRAG statuses surface as integration errors instead of silently normalizing to `indexing`.
- `/lightrag/domains/{domain_id}/graphs` and `/lightrag/domains/{domain_id}/graph/labels...` proxy to LightRAG.

## LightRAG Domain Deployment Control

Deployment control is off by default:

```env
LIGHTRAG_DEPLOY_ENABLED=false
```

When enabled, admins can manage domains through `/admin/lightrag-domains...`. Generated state lives under:

Legacy `/admin/lightrag/domains...` endpoints are removed and now return `404`.

```text
.data/lightrag/
  domains.json
  docker-compose.lightrag-domains.yml
  domains/<domain>/domain.env
  deleted/<domain>-<timestamp>/
```

Context Engine generates a separate LightRAG domains compose file and invokes `docker compose -f ...` through a fakeable runner. The generated services connect to the shared network from the root compose stack. Permanent delete remains disabled unless `LIGHTRAG_ALLOW_PERMANENT_DELETE=true`.

Each domain env selects PostgreSQL-backed LightRAG storage (`PGKVStorage`, `PGDocStatusStorage`, `PGGraphStorage`, `PGVectorStorage`) and uses shared runtime PostgreSQL credentials, while `WORKSPACE` in `domain.env` remains domain-specific for logical isolation. The root PostgreSQL image must support both `vector` and Apache `AGE`; `migrations/0002_smoke_lightrag_postgres_extensions.sql` is the smoke check for that requirement.

## Backup

Local file uploads live under `.data/uploads` by default. The helper script archives `.data`:

```bash
python -m scripts.backup
```

For production PostgreSQL backups, use `pg_dump` against `DATABASE_URL` and each `lightrag_<domain>` database. Back up the upload volume or object-store equivalent at the same consistency point.

## Restore

Restore the Context Engine database and each LightRAG domain database with `psql` or provider tooling, then restore the upload directory and `.data/lightrag` generated state from file backups.

