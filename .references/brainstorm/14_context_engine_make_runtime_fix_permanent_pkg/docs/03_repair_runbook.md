# 03 — Repair Runbook

## 1. Diagnose current state

```bash
DOMAIN=fatigue
./scripts/diagnose_lightrag_runtime.sh "$DOMAIN"
```

## 2. Inspect generated env

```bash
DOMAIN=fatigue
cat .data/lightrag/domains/$DOMAIN/domain.env | grep -E 'POSTGRES|LIGHTRAG_.*STORAGE|WORKSPACE|TIKTOKEN'
```

Expected for per-domain mode:

```env
WORKSPACE=fatigue
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage
LIGHTRAG_GRAPH_STORAGE=PGGraphStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
POSTGRES_PASSWORD=<configured lightrag password>
POSTGRES_VECTOR_INDEX_TYPE=HNSW
TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

Expected for compatibility mode:

```env
POSTGRES_DATABASE=lightrag
POSTGRES_USER=lightrag
POSTGRES_PASSWORD=lightrag
```

## 3. Verify DB role and database

```bash
docker compose exec postgres psql -U context_engine -d context_engine -c "\du"
docker compose exec postgres psql -U context_engine -d context_engine -c "SELECT datname FROM pg_database WHERE datname LIKE 'lightrag%';"
```

## 4. Verify vector extension in target DB

```bash
docker compose exec postgres psql -U context_engine -d lightrag_fatigue -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec postgres psql -U context_engine -d lightrag_fatigue -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
```

## 5. Repair through API

After implementation:

```bash
curl -X POST http://127.0.0.1:8010/admin/lightrag/domains/fatigue/repair \
  -H "Authorization: Bearer $TOKEN"
```

## 6. Re-test from inside API container

```bash
docker compose exec api python - <<'PY'
import httpx, socket

host = "context_engine_lightrag_fatigue"
print(socket.gethostbyname_ex(host))
print(httpx.get("http://context_engine_lightrag_fatigue:9621/health", timeout=10).text)
PY
```

If the service name is `lightrag_fatigue`, test that too:

```bash
docker compose exec api python - <<'PY'
import httpx, socket

host = "lightrag_fatigue"
print(socket.gethostbyname_ex(host))
print(httpx.get("http://lightrag_fatigue:9621/health", timeout=10).text)
PY
```

## 7. Remove legacy container once managed container is healthy

Once `context_engine_lightrag_fatigue` is healthy and all traffic points to the managed domain URL, stop/remove old unmanaged containers that still use `POSTGRES_USER=lightrag`.
