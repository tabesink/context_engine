# Context Engine

Backend-only multi-user hybrid RAG application.

Semantic retrieval is mandatory remote LightRAG. This service keeps local navigation retrieval (`mode=navigation`) for page/section lookups, but it does not provide a local semantic fallback.

## Prerequisites

- **Python 3.11+** (see `requires-python` in `pyproject.toml`)
- **PostgreSQL** and **Redis** at the URLs in `.env` (the host-first example uses `localhost:5438` and `localhost:6386`; Compose maps those to in-network service URLs for containers)

First-time setup for both options:

```powershell
copy .env.example .env
```

Optional overlays for LightRAG deployment/provider settings are available in `.env.lightrag-deploy.example` and `.env.lightrag-provider.example`.

Edit `.env` if your database or Redis URLs differ. Admin login is configured with `SEED_ADMIN_USERNAME` and `SEED_ADMIN_PASSWORD`.

`DATABASE_URL` is required. Context Engine supports PostgreSQL as the runtime database for local development, staging, and production; sqlite is reserved only for explicit isolated tests.

Port and host settings are centralized in root `.env` for local runs:
- `API_HOST` / `API_PORT`
- `CLIENT_HOST` / `CLIENT_PORT`
- `LIGHTRAG_HOST`
- `NEXT_PUBLIC_API_URL` (canonical frontend API base URL; `NEXT_PUBLIC_BACKEND_BASE_URL` remains a compatibility alias)

---

## Option A: Docker Compose

Runs PostgreSQL, Redis, the API, the worker, and the LightRAG status poller together.

```powershell
docker compose up --build
```

- API: `http://localhost:8010`
- PostgreSQL: `localhost:5438`
- Redis: `localhost:6386` (host port; container still listens on 6379)

Seed the admin user (first run, or after changing seed credentials):

```powershell
docker compose exec api python -m scripts.seed_admin
```

Health check:

```powershell
curl http://localhost:8010/health
```

With `INDEX_JOBS_INLINE=false` (as in `.env.example`), uploads and reindex requests enqueue jobs; the `worker` service processes them and the `status-poller` service keeps pending LightRAG indexing states synchronized.
Set `INDEX_JOBS_INLINE=true` if you want indexing in-process without a worker.

For live-reload development inside Compose, run with the dev override:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

---

## Option B: Local API (uvicorn)

Use your own Python for the API. You still need PostgreSQL and Redis running and matching `DATABASE_URL` and `REDIS_URL` in `.env`.

**Start only databases with Docker** (optional):

```powershell
docker compose up postgres redis -d
```

**Install and run:**

```powershell
python -m pip install --user -e .
python -m scripts.seed_admin
uvicorn app.main:create_app --factory --reload --port 8010
```

For tests and dev tooling, install with optional dependencies:

```powershell
python -m pip install --user -e ".[dev]"
```

If `INDEX_JOBS_INLINE=false`, run a worker in another terminal (same as the Compose worker):

```powershell
python -m app.workers.worker
```

Run a second terminal for the status poller:

```powershell
python -m app.workers.status_poller
```

Or set `INDEX_JOBS_INLINE=true` in `.env` for local development without separate worker/poller processes.

Health check:

```powershell
curl http://localhost:8010/health
```

Readiness check:

```powershell
curl http://localhost:8010/health/readiness
```

---

## Terminal Application (Deprecated)

The local terminal UI/CLI is deprecated and no longer a supported workflow.

- Do not rely on `context-engine` / `context-tui` for production or active development workflows.
- Use the HTTP API directly (and web/admin surfaces where available) for supported behavior.
- Legacy CLI/TUI code remains in-repo temporarily for transition/testing continuity.

## Test

```powershell
python -m pytest -q
```

Tests set `INDEX_JOBS_INLINE=true` so indexing completes without a Redis worker.


# GitNexus 
Run webui for gitnexus using cmd:
    npx gitnexus server 

