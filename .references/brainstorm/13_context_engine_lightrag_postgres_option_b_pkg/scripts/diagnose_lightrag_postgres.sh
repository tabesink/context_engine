#!/usr/bin/env bash
set -euo pipefail

DOMAIN_ID="${1:-fatigue}"
DOMAIN_ENV=".data/lightrag/domains/${DOMAIN_ID}/domain.env"
SERVICE_NAME="lightrag_${DOMAIN_ID}"

printf '\n== Domain env: %s ==\n' "$DOMAIN_ENV"
if [[ -f "$DOMAIN_ENV" ]]; then
  grep -E '^(WORKSPACE|LIGHTRAG_.*STORAGE|POSTGRES_)' "$DOMAIN_ENV" || true
else
  echo "Missing $DOMAIN_ENV"
fi

printf '\n== Postgres roles containing lightrag ==\n'
docker compose exec -T postgres psql -U "${POSTGRES_USER:-context_engine}" -d "${POSTGRES_DB:-context_engine}" -c "SELECT rolname FROM pg_roles WHERE rolname LIKE 'lightrag%';" || true

printf '\n== Postgres databases containing lightrag ==\n'
docker compose exec -T postgres psql -U "${POSTGRES_USER:-context_engine}" -d "${POSTGRES_DB:-context_engine}" -c "SELECT datname FROM pg_database WHERE datname LIKE 'lightrag%';" || true

printf '\n== Docker DNS from api ==\n'
docker compose exec -T api getent hosts "$SERVICE_NAME" || true

printf '\n== Docker DNS from worker ==\n'
docker compose exec -T worker getent hosts "$SERVICE_NAME" || true

printf '\n== LightRAG health from api ==\n'
docker compose exec -T api python - <<PY || true
import httpx
url = "http://${SERVICE_NAME}:9621/health"
try:
    r = httpx.get(url, timeout=5)
    print(url, r.status_code, r.text[:500])
except Exception as exc:
    print(url, type(exc).__name__, exc)
PY

printf '\n== Recent Postgres auth errors ==\n'
docker compose logs --tail=200 postgres | grep -E 'FATAL|password authentication|Role "lightrag|lightrag_' || true
