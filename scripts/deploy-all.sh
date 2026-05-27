#!/usr/bin/env bash
# Start backend and frontend dev servers together.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/deploy-all.sh [server options...]

Starts:
  - server via scripts/deploy-server.sh
  - client via npm run dev in ./client

Any options are passed through to scripts/deploy-server.sh.
Examples:
  scripts/deploy-all.sh --dev
  scripts/deploy-all.sh --no-docker --refresh-deps
EOF
}

server_args=("$@")
for arg in "${server_args[@]}"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    usage
    exit 0
  fi
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
server_script="$repo_root/scripts/deploy-server.sh"
client_dir="$repo_root/client"
env_file="$repo_root/.env"

if [[ ! -x "$server_script" ]]; then
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

server_pid=""
client_pid=""

cleanup() {
  local exit_code=$?

  if [[ -n "$server_pid" ]] && kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$client_pid" ]] && kill -0 "$client_pid" >/dev/null 2>&1; then
    kill "$client_pid" >/dev/null 2>&1 || true
  fi

  wait >/dev/null 2>&1 || true
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

printf '%s\n' "Starting server..."
"$server_script" "${server_args[@]}" &
server_pid=$!

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

printf 'Server PID: %s\n' "$server_pid"
printf 'Client PID: %s\n' "$client_pid"
printf 'API host:port: %s:%s\n' "$api_host" "$api_port"
printf 'Client host:port: %s:%s\n' "$client_host" "$client_port"
printf 'Client API base: %s\n' "$client_api_base"
printf '%s\n' "Press Ctrl+C to stop both processes."

wait -n "$server_pid" "$client_pid"

