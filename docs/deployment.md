# Deployment Notes

The supported local deployment uses Docker Compose with PostgreSQL, Redis, the API, and one worker. Compose does not start LightRAG; when enabled, LightRAG is an external HTTP service configured with `LIGHTRAG_*` environment variables.

## Required Environment

Copy `.env.example` and change production-sensitive values before running outside local development.

```bash
cp .env.example .env
```

Important settings:

- `SECRET_KEY`: strong random value; never use the development default in production.
- `DATABASE_URL`: SQLAlchemy URL. Compose expects PostgreSQL at `postgresql+psycopg://context_engine:context_engine@postgres:5432/context_engine` from inside containers; local non-compose runs default to SQLite if unset.
- `REDIS_URL`: Redis URL. Compose uses `redis://redis:6379/0` from inside containers.
- `INDEX_JOBS_INLINE`: `false` for worker-backed indexing; `true` only for deterministic local tests/dev flows.
- `STORAGE_ROOT`: persistent mounted upload directory.
- `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD`: first admin credentials for `scripts.seed_admin`.
- `ALLOWED_ORIGINS`: comma-separated CORS origins, or `*` for local development.
- `LIGHTRAG_ENABLED`: `false` by default. Set to `true` only when a compatible LightRAG service is reachable.
- `LIGHTRAG_BASE_URL`: base URL of the external LightRAG service, default `http://localhost:9621`.
- `LIGHTRAG_API_KEY`: optional bearer token sent to LightRAG.
- `LIGHTRAG_DOMAIN`: default LightRAG domain name.
- `LIGHTRAG_DOMAIN_MANIFEST`: optional JSON manifest for per-domain base URLs/API keys.
- `LIGHTRAG_TIMEOUT_SECONDS`: HTTP timeout for LightRAG calls.

## First Run With Compose

For containerized API/worker runs, make sure `.env` uses service names for internal URLs:

```env
DATABASE_URL=postgresql+psycopg://context_engine:context_engine@postgres:5432/context_engine
REDIS_URL=redis://redis:6379/0
INDEX_JOBS_INLINE=false
```

Then start the stack:

```bash
docker compose up --build -d postgres redis
docker compose run --rm api python -m scripts.seed_admin
docker compose up --build
```

The `worker` service must stay up when `INDEX_JOBS_INLINE=false`. It consumes indexing jobs and moves them through `queued`, `running`, `succeeded`, or `failed`.

## Local Non-Compose Run

For a quick local API run, install the package and run Uvicorn from the repository root:

```bash
python -m pip install -e ".[dev]"
python -m uvicorn app.main:create_app --factory --reload
```

If no `.env` overrides `DATABASE_URL`, the app uses SQLite at `.data/context_engine.db`.

## LightRAG

LightRAG is optional and external:

```env
LIGHTRAG_ENABLED=true
LIGHTRAG_BASE_URL=http://localhost:9621
LIGHTRAG_API_KEY=
```

When enabled:

- `auto`, `semantic`, and `hybrid` query modes use remote LightRAG.
- `navigation` query mode remains local.
- Admin uploads are forwarded to LightRAG and may return `job_id: null` because ingestion is owned by the remote service.
- `/graphs` and `/graph/label/...` proxy to LightRAG.

When disabled, local upload/index/query behavior remains active and graph proxy routes return `LightRAG is disabled`.

## Backup

Local file uploads live under `.data/uploads` by default. The helper script archives `.data`:

```bash
python -m scripts.backup
```

For production PostgreSQL backups, use `pg_dump` against `DATABASE_URL`. Back up the upload volume or object-store equivalent at the same consistency point.

## Restore

Restore the database with `psql` or provider tooling, then restore the upload directory from the file archive. If LightRAG is enabled, restore or rebuild the external LightRAG service/index separately because it is not part of this Compose stack.

