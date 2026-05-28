#!/usr/bin/env bash
# Start backend and frontend dev servers together.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/deploy-all.sh [--local-api] [local-api options...]

Default mode (recommended):
  - backend via docker compose (postgres, redis, migrate, api, worker, status-poller)
  - client via npm run dev in ./client

Optional local API mode:
  --local-api            Run backend via scripts/deploy-server.sh instead of compose
  --dev                  (local-api only) install editable dev dependencies (.[dev])
  --no-docker            (local-api only) skip docker compose startup/readiness checks
  --refresh-deps         (local-api only) force reinstall of editable dependencies

Examples:
  scripts/deploy-all.sh
  scripts/deploy-all.sh --local-api --dev
EOF
}

backend_mode="compose"
server_args=()
for arg in "$@"; do
  case "$arg" in
    --local-api)
      backend_mode="local"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --dev|--no-docker|--refresh-deps)
      server_args+=("$arg")
      ;;
    *)
      printf 'Unknown argument: %s\n\n' "$arg" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$backend_mode" == "compose" && ${#server_args[@]} -gt 0 ]]; then
  printf '%s\n' "Local API flags (--dev/--no-docker/--refresh-deps) require --local-api." >&2
  exit 1
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
server_script="$repo_root/scripts/deploy-server.sh"
client_dir="$repo_root/client"
env_file="$repo_root/.env"

if [[ "$backend_mode" == "local" && ! -x "$server_script" ]]; then
  printf 'Missing or non-executable server script: %s\n' "$server_script" >&2
  exit 1
fi

if [[ ! -f "$client_dir/package.json" ]]; then
  printf 'Missing client package.json: %s\n' "$client_dir/package.json" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  printf '%s\n' "npm is required to run the client." >&2
  exit 1
fi

read_env_value() {
  local key="$1"
  local file="$2"
  if [[ ! -f "$file" ]]; then
    return
  fi
  local line
  line="$(sed -nE "s/^[[:space:]]*${key}[[:space:]]*=(.*)$/\\1/p" "$file" | sed -n '1p' || true)"
  if [[ -z "$line" ]]; then
    return
  fi
  line="$(printf '%s' "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  if [[ -z "$line" ]]; then
    return
  fi
  printf '%s' "$line"
}

api_host="${API_HOST:-$(read_env_value API_HOST "$env_file")}"
api_host="${api_host:-127.0.0.1}"
api_port="${API_PORT:-$(read_env_value API_PORT "$env_file")}"
api_port="${api_port:-8010}"
client_host="${CLIENT_HOST:-$(read_env_value CLIENT_HOST "$env_file")}"
client_host="${client_host:-127.0.0.1}"
client_port="${CLIENT_PORT:-$(read_env_value CLIENT_PORT "$env_file")}"
client_port="${client_port:-3007}"

client_api_base="${NEXT_PUBLIC_API_URL:-}"
if [[ -z "$client_api_base" ]]; then
  client_api_base="${NEXT_PUBLIC_BACKEND_BASE_URL:-}"
fi
if [[ -z "$client_api_base" ]]; then
  client_api_base="$(read_env_value NEXT_PUBLIC_API_URL "$env_file")"
fi
if [[ -z "$client_api_base" ]]; then
  client_api_base="$(read_env_value NEXT_PUBLIC_BACKEND_BASE_URL "$env_file")"
fi
if [[ -z "$client_api_base" ]]; then
  client_api_base="http://${api_host}:${api_port}"
fi

compose_pid=""
server_pid=""
client_pid=""
seed_pid=""

cleanup() {
  local exit_code=$?

  if [[ -n "$client_pid" ]] && kill -0 "$client_pid" >/dev/null 2>&1; then
    kill "$client_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$server_pid" ]] && kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$seed_pid" ]] && kill -0 "$seed_pid" >/dev/null 2>&1; then
    kill "$seed_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$compose_pid" ]] && kill -0 "$compose_pid" >/dev/null 2>&1; then
    kill -INT "$compose_pid" >/dev/null 2>&1 || kill "$compose_pid" >/dev/null 2>&1 || true
  fi

  wait >/dev/null 2>&1 || true
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

if [[ "$backend_mode" == "compose" ]]; then
  printf '%s\n' "Starting backend via docker compose (api + worker + status-poller)..."
  (cd "$repo_root" && docker compose up --build) &
  compose_pid=$!

  api_base_url="http://${api_host}:${api_port}"
  (
    cd "$repo_root"
    for _ in $(seq 1 90); do
      if curl -fsS "${api_base_url}/health" >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done
    docker compose exec -T api python -c "from app.seed import ensure_seed_admin; user = ensure_seed_admin(sync_password=True); print(f'Seed admin ready: {user.email}')"
  ) &
  seed_pid=$!
else
  printf '%s\n' "Starting backend via local API script..."
  "$server_script" "${server_args[@]}" &
  server_pid=$!
fi

printf '%s\n' "Starting client..."
(
  cd "$client_dir"
  PORT="$client_port" \
  HOSTNAME="$client_host" \
  NEXT_PUBLIC_API_URL="$client_api_base" \
  NEXT_PUBLIC_BACKEND_BASE_URL="$client_api_base" \
  NEXT_PUBLIC_API_PORT="$api_port" \
  npm run dev
) &
client_pid=$!

if [[ -n "$compose_pid" ]]; then
  printf 'Compose PID: %s\n' "$compose_pid"
else
  printf 'Server PID: %s\n' "$server_pid"
fi
printf 'Client PID: %s\n' "$client_pid"
printf 'API host:port: %s:%s\n' "$api_host" "$api_port"
printf 'Client host:port: %s:%s\n' "$client_host" "$client_port"
printf 'Client API base: %s\n' "$client_api_base"
seed_username="$(read_env_value SEED_ADMIN_USERNAME "$env_file")"
seed_username="${seed_username:-admin}"
seed_password="$(read_env_value SEED_ADMIN_PASSWORD "$env_file")"
seed_password="${seed_password:-admin-password}"
printf 'Login: %s / %s (from .env SEED_ADMIN_*)\n' "$seed_username" "$seed_password"
printf '%s\n' "Press Ctrl+C to stop both processes."

if [[ -n "$compose_pid" ]]; then
  wait -n "$compose_pid" "$client_pid"
else
  wait -n "$server_pid" "$client_pid"
fi

