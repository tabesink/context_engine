#!/usr/bin/env bash
# Option B: local Postgres/Redis via Docker (optional), editable install, seed admin, uvicorn.
set -euo pipefail

dev=false
no_docker=false
refresh_deps=false

usage() {
  cat <<'EOF'
Usage: scripts/deploy-server.sh [--dev] [--no-docker] [--refresh-deps]

Options:
  --dev           Install editable dev dependencies (.[dev]).
  --no-docker     Skip docker compose startup/readiness checks.
  --refresh-deps  Force reinstall of editable dependencies into .venv.
  -h, --help      Show this help message.
EOF
}

while (($# > 0)); do
  case "$1" in
    --dev)
      dev=true
      ;;
    --no-docker)
      no_docker=true
      ;;
    --refresh-deps)
      refresh_deps=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' "uv is required for Option B. Install from https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  printf '%s\n' "Created .env from .env.example - edit if needed."
fi

api_port="8000"
if [[ -f .env ]]; then
  api_port_line="$(sed -nE 's/^[[:space:]]*API_PORT[[:space:]]*=(.*)$/\1/p' .env | sed -n '1p' || true)"
  if [[ -n "$api_port_line" ]]; then
    value="$(printf '%s' "$api_port_line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    if [[ -n "$value" ]]; then
      api_port="$value"
    fi
  fi
fi

if [[ "$no_docker" == false ]]; then
  docker compose up postgres redis -d
  ok=false
  for _ in {1..45}; do
    if docker compose exec -T postgres pg_isready -U context_engine -d context_engine >/dev/null 2>&1; then
      ok=true
      break
    fi
    sleep 1
  done
  if [[ "$ok" == false ]]; then
    printf '%s\n' "Postgres not ready (docker compose postgres)." >&2
    exit 1
  fi
fi

venv_dir=".venv"
venv_python="$venv_dir/bin/python"

if [[ ! -x "$venv_python" ]]; then
  uv venv "$venv_dir"
fi

base_marker="$venv_dir/.deps-base.stamp"
dev_marker="$venv_dir/.deps-dev.stamp"

needs_install=false
if [[ "$refresh_deps" == true || ! -f "$base_marker" ]]; then
  needs_install=true
fi
if [[ "$dev" == true && ! -f "$dev_marker" ]]; then
  needs_install=true
fi

if [[ "$needs_install" == true ]]; then
  spec="."
  if [[ "$dev" == true ]]; then
    spec=".[dev]"
  fi
  uv pip install --python "$venv_python" -e "$spec"
  if [[ ! -f "$base_marker" ]]; then
    touch "$base_marker"
  fi
  if [[ "$dev" == true && ! -f "$dev_marker" ]]; then
    touch "$dev_marker"
  fi
fi

"$venv_python" -m alembic upgrade head
"$venv_python" -m scripts.seed_admin
"$venv_python" -m uvicorn app.main:create_app --factory --reload --port "$api_port"
