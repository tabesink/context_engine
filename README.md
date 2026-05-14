# Context Engine

Backend-only multi-user hybrid RAG application.

## Run Locally

```powershell
python -m pip install --user -e .
copy .env.example .env
python -m scripts.seed_admin
uvicorn app.main:create_app --factory --reload
```

Health check:

```powershell
curl http://localhost:8000/health
```

## Test

```powershell
python -m pytest -q
```

Tests set `INDEX_JOBS_INLINE=true` so indexing completes without a Redis worker.

## Docker Compose

```powershell
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

With `INDEX_JOBS_INLINE=false`, upload and reindex requests create queued jobs. Keep the `worker` service running to process them.

## Default Admin

Configured in `.env`:

- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`

Create the admin with:

```powershell
python -m scripts.seed_admin
```

