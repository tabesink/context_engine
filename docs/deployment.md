# Deployment Notes

The supported local deployment uses Docker Compose with PostgreSQL, Redis, the API, and one worker. Runtime LightRAG remains an external HTTP service configured with `LIGHTRAG_*` variables. Context Engine can also optionally manage same-machine LightRAG domain containers through admin-only deployment-control APIs.

## Required Environment

Copy `.env.example` and change production-sensitive values before running outside local development.

```bash
cp .env.example .env
```

Important settings:

- `SECRET_KEY`: strong random value; never use the development default in production.
- `PUBLISH_POSTGRES_PORT`, `PUBLISH_REDIS_PORT`, `API_PORT`: host port mappings exposed by Compose (defaults in `docker-compose.yml` fall back to `5432`, `6386`, and `8000`; `.env.example` uses different publish ports—keep `DATABASE_URL` / `REDIS_URL` consistent when connecting from the host).
- `DATABASE_URL`: SQLAlchemy URL. Compose expects PostgreSQL at `postgresql+psycopg://context_engine:context_engine@postgres:5432/context_engine` from inside containers; local non-compose runs default to SQLite if unset.
- `REDIS_URL`: Redis URL. Compose uses `redis://redis:6379/0` from inside containers.
- `CONTEXT_ENGINE_API_BASE_URL` (optional): default base URL the `context-engine` terminal client uses when `--api-base-url` is omitted. This is independent of `API_PORT`: if the API listens on host port `8010` (as in `.env.example`), set this to `http://127.0.0.1:8010` or pass `--api-base-url` accordingly—the CLI launcher default remains `http://127.0.0.1:8000` when the variable is unset.
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
- `LIGHTRAG_DEPLOY_ENABLED`: gates **mutating** LightRAG domain deployment APIs (`/admin/lightrag/domains...`). The read-only `GET /lightrag/domains` listing remains available to authenticated users so clients can choose `lightrag_domain_id` when manifests exist.
- `LIGHTRAG_DEPLOY_ROOT`, `LIGHTRAG_DOMAINS_ROOT`, `LIGHTRAG_DOMAINS_MANIFEST`, `LIGHTRAG_COMPOSE_FILE`, `LIGHTRAG_DELETED_ROOT`: generated deployment state under `.data/lightrag`.
- `LIGHTRAG_DEFAULT_PORT_START`, `LIGHTRAG_DEFAULT_CONTAINER_PORT`, `LIGHTRAG_DOCKER_NETWORK`, `LIGHTRAG_DOMAIN_ENV_FILENAME`: port allocation defaults, compose bridge network name, and per-domain env file name.
- Optional dependency injection for compose services: `LIGHTRAG_DOCKERFILE`, `LIGHTRAG_BUILD_CONTEXT`, `LIGHTRAG_POSTGRES_URL`, `LIGHTRAG_REDIS_URL`, `LIGHTRAG_NEO4J_*` when generated domain env templates need them.
- `LIGHTRAG_ARCHIVE_DELETED_DOMAINS`, `LIGHTRAG_ALLOW_PERMANENT_DELETE`: archival versus hard delete semantics for removed domains.
- `LIGHTRAG_IMAGE`, `LIGHTRAG_DOCKER_COMPOSE_BIN`, `LIGHTRAG_DOCKER_EXECUTION_MODE`, `LIGHTRAG_DOCKER_TIMEOUT_SECONDS`: image and Docker Compose execution settings.

In `app/core/config.py`, `lightrag_enabled` and `lightrag_deploy_enabled` default to `false` for safe standalone runs. The checked-in `.env.example` enables both for integration-style local setups; tighten those flags for environments that must not assume LightRAG or Docker Compose control.

## First Run With Compose

For containerized API/worker runs, make sure `.env` uses service names for internal URLs:

```env
DATABASE_URL=postgresql+psycopg://context_engine:context_engine@postgres:5432/context_engine
REDIS_URL=redis://redis:6379/0
INDEX_JOBS_INLINE=false
```

Then start the stack and seed admin (adjust service name if your compose file differs):

```bash
docker compose up --build -d postgres redis
docker compose up --build
docker compose exec api python -m scripts.seed_admin
```

Alternatively, `docker compose run --rm api python -m scripts.seed_admin` works before the stack is fully up; use whichever fits your workflow.

The `worker` service must stay up when `INDEX_JOBS_INLINE=false`. It consumes indexing jobs and moves them through `queued`, `running`, `succeeded`, or `failed`.

## Published Ports And `.env.example`

Compose maps **host** ports from your `.env` (`PUBLISH_POSTGRES_PORT`, `PUBLISH_REDIS_PORT`, `API_PORT`). The checked-in `.env.example` uses non-default values (PostgreSQL and Redis published on alternate localhost ports, and a non-`8000` API port). Set `DATABASE_URL` and `REDIS_URL` to those same localhost ports when you run tooling on the host; services **inside** the Compose network keep using hostnames `postgres` and `redis` with container ports `5432` and `6379`.

## Local Non-Compose Run

For a quick local API run, install the package and run Uvicorn from the repository root:

```bash
python -m pip install -e ".[dev]"
uvicorn app.main:create_app --factory --reload
```

If no `.env` overrides `DATABASE_URL`, the app uses SQLite at `.data/context_engine.db`.

## Terminal Client (`context-engine`)

After `pip install -e .`, the supported CLI is the interactive TUI (`context-engine` and `context-tui` entry points invoke the same code):

```bash
context-engine
```

- **Backend URL**: `--api-base-url` or `CONTEXT_ENGINE_API_BASE_URL` (defaults in `cli/config.py` to `http://127.0.0.1:8000` unless overridden). Align this with the API’s real host port (`API_PORT` / `.env`), since `.env.example` often publishes the API on non-`8000` ports.
- **Credentials**: stored under `--config-dir` or the default `~/.context-engine/cli/`; `--keyring` / `--no-keyring` toggle OS keyring vs file-backed storage.

The UI calls the backend over HTTP via `cli/api_client.py` and helpers in `cli/services/`; screen layout builders under `cli/screens/` and `cli/renderers/` are composed into the Rich TUI under `cli/tui/`, not a second transport.

## LightRAG Runtime

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

When disabled, local upload/index/query behavior remains active and graph proxy routes respond with HTTP `400` and detail `LightRAG is disabled`.

## LightRAG Domain Deployment Control

Deployment control is off by default:

```env
LIGHTRAG_DEPLOY_ENABLED=false
```

When enabled, admins can manage domains through `/admin/lightrag/domains...` or the terminal UI. Generated state lives under:

```text
.data/lightrag/
  domains.json
  docker-compose.lightrag-domains.yml
  domains/<domain>/domain.env
  deleted/<domain>-<timestamp>/
```

Context Engine does not rewrite the root `docker-compose.yml`. It generates a separate LightRAG domains compose file and invokes `docker compose -f ...` through a fakeable runner. Permanent delete remains disabled unless `LIGHTRAG_ALLOW_PERMANENT_DELETE=true`.

## Backup

Local file uploads live under `.data/uploads` by default. The helper script archives `.data`:

```bash
python -m scripts.backup
```

For production PostgreSQL backups, use `pg_dump` against `DATABASE_URL`. Back up the upload volume or object-store equivalent at the same consistency point.

## Restore

Restore the database with `psql` or provider tooling, then restore the upload directory from the file archive. If LightRAG is enabled, restore or rebuild the external LightRAG service/index separately because it is not part of this Compose stack.

