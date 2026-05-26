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

Edit `.env` if your database or Redis URLs differ. Admin login is configured with `SEED_ADMIN_USERNAME` and `SEED_ADMIN_PASSWORD`.

`DATABASE_URL` is required. Context Engine supports PostgreSQL as the runtime database for local development, staging, and production; sqlite is reserved only for explicit isolated tests.

---

## Option A: Docker Compose

Runs PostgreSQL, Redis, the API, and the worker together.

```powershell
docker compose up --build
```

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5438`
- Redis: `localhost:6386` (host port; container still listens on 6379)

Seed the admin user (first run, or after changing seed credentials):

```powershell
docker compose exec api python -m scripts.seed_admin
```

Health check:

```powershell
curl http://localhost:8000/health
```

With `INDEX_JOBS_INLINE=false` (as in `.env.example`), uploads and reindex requests enqueue jobs; the `worker` service processes them. Set `INDEX_JOBS_INLINE=true` if you want indexing in-process without a worker.

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
uvicorn app.main:create_app --factory --reload
```

For tests and dev tooling, install with optional dependencies:

```powershell
python -m pip install --user -e ".[dev]"
```

If `INDEX_JOBS_INLINE=false`, run a worker in another terminal (same as the Compose worker):

```powershell
python -m app.workers.worker
```

Or set `INDEX_JOBS_INLINE=true` in `.env` for local development without a separate worker.

Health check:

```powershell
curl http://localhost:8000/health
```

---

## Terminal Application

After `pip install -e .`, launch the interactive terminal UI with:

```powershell
context-engine
```

or:

```powershell
context-tui
```

The terminal UI is the supported local CLI workflow for login/session, documents, retrieval, LightRAG views, admin document actions, jobs, observability, and health/readiness checks.

## Test

```powershell
python -m pytest -q
```

Tests set `INDEX_JOBS_INLINE=true` so indexing completes without a Redis worker.
