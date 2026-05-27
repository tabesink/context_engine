# 03 — Immediate Repair Runbook

Use this before the code fix lands to confirm and unblock local development.

## 1. Inspect generated domain env

```bash
cat .data/lightrag/domains/fatigue/domain.env | grep -E "POSTGRES|LIGHTRAG_.*STORAGE|WORKSPACE"
```

If you see:

```env
POSTGRES_USER=lightrag
```

then the log is explained: Postgres does not have that role.

## 2. Inspect roles in Postgres

```bash
docker compose exec postgres psql -U context_engine -d context_engine -c "\du"
```

## 3. Fast temporary fix using current broken env

If the domain env currently says `POSTGRES_USER=lightrag` and `POSTGRES_DATABASE=context_engine`, temporarily create the role:

```bash
docker compose exec -T postgres psql -U context_engine -d context_engine < sql/local_repair_create_lightrag_role.sql
```

This is only a triage fix. The clean implementation should use per-domain DB/user.

## 4. Preferred repair after implementation

After Option B is implemented:

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8010/admin/lightrag/domains/fatigue/repair
```

Then verify:

```bash
cat .data/lightrag/domains/fatigue/domain.env | grep -E "POSTGRES_DATABASE|POSTGRES_USER|POSTGRES_HOST"
```

Expected:

```env
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
POSTGRES_HOST=postgres
```

## 5. Restart/recreate domain manually if needed

```bash
docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml up -d --force-recreate lightrag_fatigue
```

## 6. Confirm container-to-container access

```bash
docker compose exec api getent hosts lightrag_fatigue
docker compose exec worker getent hosts lightrag_fatigue
```

```bash
docker compose exec api python - <<'PY'
import httpx
for url in ["http://lightrag_fatigue:9621/health", "http://lightrag_fatigue:9621/"]:
    try:
        r = httpx.get(url, timeout=5)
        print(url, r.status_code, r.text[:200])
    except Exception as e:
        print(url, type(e).__name__, e)
PY
```

