# 04 — Acceptance Tests

## Test 1 — Domain env uses provisioned per-domain credentials

Create domain:

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"fatigue","display_name":"Fatigue"}' \
  http://localhost:8010/admin/lightrag/domains
```

Check env:

```bash
grep -E "POSTGRES_DATABASE|POSTGRES_USER|POSTGRES_PASSWORD" .data/lightrag/domains/fatigue/domain.env
```

Expected:

```env
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
POSTGRES_PASSWORD=<configured LIGHTRAG_POSTGRES_PASSWORD>
```

## Test 2 — Role exists

```bash
docker compose exec postgres psql -U context_engine -d context_engine -c "SELECT rolname FROM pg_roles WHERE rolname='lightrag_fatigue';"
```

Expected: one row.

## Test 3 — Database exists

```bash
docker compose exec postgres psql -U context_engine -d context_engine -c "SELECT datname FROM pg_database WHERE datname='lightrag_fatigue';"
```

Expected: one row.

## Test 4 — Extensions available

```bash
docker compose exec postgres psql -U context_engine -d lightrag_fatigue -c "SELECT extname FROM pg_extension WHERE extname IN ('vector','age');"
```

Expected:

```text
vector
age
```

If `age` is not available but graph storage is set to `PGGraphStorage`, the custom Postgres image must be corrected or graph storage must not be Postgres AGE-backed.

## Test 5 — Repair is idempotent

```bash
for i in 1 2 3; do
  curl -s -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    http://localhost:8010/admin/lightrag/domains/fatigue/repair | jq .status
done
```

Expected: `"succeeded"` each time.

## Test 6 — Upload does not emit role-missing Postgres error

1. Start domain.
2. Upload a document.
3. Watch logs:

```bash
docker compose logs -f postgres worker api | grep -E "lightrag|FATAL|password authentication|Role"
```

Expected: no `Role "lightrag" does not exist` error.

