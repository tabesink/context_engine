# Context Engine

Backend-only multi-user hybrid RAG application.

## Prerequisites

- **Python 3.11+** (see `requires-python` in `pyproject.toml`)
- **PostgreSQL** and **Redis** at the URLs in `.env` (defaults use `localhost:5432` and `localhost:6386` when using Compose)

First-time setup for both options:

```powershell
copy .env.example .env
```

Edit `.env` if your database or Redis URLs differ. Admin login is configured with `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD`.

---

## Option A: Docker Compose

Runs PostgreSQL, Redis, the API, and the worker together.

```powershell
docker compose up --build
```

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
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

## CLI

After `pip install -e .`, the Typer CLI is available as `ragcli` (`ragcli --help`).

## Test

```powershell
python -m pytest -q
```

Tests set `INDEX_JOBS_INLINE=true` so indexing completes without a Redis worker.
