#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-fatigue}"
SERVICE_A="context_engine_lightrag_${DOMAIN}"
SERVICE_B="lightrag_${DOMAIN}"
ENV_FILE=".data/lightrag/domains/${DOMAIN}/domain.env"

echo "== Context Engine LightRAG runtime diagnosis =="
echo "Domain: $DOMAIN"
echo

echo "== domain.env =="
if [[ -f "$ENV_FILE" ]]; then
  grep -E "^(WORKSPACE|LIGHTRAG_.*STORAGE|POSTGRES_|TIKTOKEN_CACHE_DIR)" "$ENV_FILE" || true
else
  echo "Missing $ENV_FILE"
fi
echo

echo "== Postgres roles =="
docker compose exec -T postgres psql -U "${POSTGRES_USER:-context_engine}" -d "${POSTGRES_DB:-context_engine}" -c "\du" || true
echo

echo "== LightRAG databases =="
docker compose exec -T postgres psql -U "${POSTGRES_USER:-context_engine}" -d "${POSTGRES_DB:-context_engine}" -c "SELECT datname FROM pg_database WHERE datname LIKE 'lightrag%';" || true
echo

for DB in "lightrag" "lightrag_${DOMAIN}"; do
  echo "== Extensions in $DB =="
  docker compose exec -T postgres psql -U "${POSTGRES_USER:-context_engine}" -d "$DB" -c "SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector','age');" || true
  echo
done

echo "== Docker containers =="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "lightrag|context-engine|postgres|redis" || true
echo

echo "== API DNS checks =="
for HOST in "$SERVICE_A" "$SERVICE_B"; do
  docker compose exec -T api python - <<PY || true
import socket
host = "$HOST"
try:
    print(host, socket.gethostbyname_ex(host))
except Exception as e:
    print(host, type(e).__name__, e)
PY
done
echo

echo "== Health checks from host =="
for PORT in 9621 9622 9623; do
  echo "Port $PORT"
  curl -fsS "http://127.0.0.1:${PORT}/health" || true
  echo
done

echo "== Recent Postgres LightRAG errors =="
docker compose logs postgres --tail=200 | grep -E "lightrag|FATAL|vector|AGE|age" || true
