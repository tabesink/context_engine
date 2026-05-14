# Deployment Notes

V1 deployment uses Docker Compose with PostgreSQL, Redis, the API, and one worker.

## Required Environment

- `SECRET_KEY`: strong random value.
- `DATABASE_URL`: PostgreSQL SQLAlchemy URL.
- `REDIS_URL`: Redis URL.
- `INDEX_JOBS_INLINE`: `false` for production so uploads enqueue Redis jobs.
- `STORAGE_ROOT`: persistent mounted upload directory.
- `SEED_ADMIN_EMAIL`: first admin email.
- `SEED_ADMIN_PASSWORD`: first admin password.

## First Run

```powershell
copy .env.example .env
docker compose up --build -d postgres redis
docker compose run --rm api python -m scripts.seed_admin
docker compose up --build
```

The `worker` service must stay up. It consumes the `indexing` queue and moves jobs through `queued`, `running`, `succeeded`, or `failed`.

## Backup

Local file uploads live under `.data/uploads` by default. The current helper script archives `.data`.

```powershell
python -m scripts.backup
```

For production Postgres backups, use `pg_dump` against `DATABASE_URL`.

## Restore

Restore the database with `psql` or provider tooling, then restore the upload directory from the file archive.

