#!/usr/bin/env bash
# Bootstrap the context-engine CLI into repo-local .venv using uv.
set -euo pipefail

dev=false
refresh_deps=false
api_base_url=""

usage() {
  cat <<'EOF'
Usage: scripts/deploy-cli.sh [--dev] [--refresh-deps] [--api-base-url <url>]

Options:
  --dev                  Install editable dev dependencies (.[dev]).
  --refresh-deps         Force reinstall of editable dependencies into .venv.
  --api-base-url <url>   Override API base URL.
  -h, --help             Show this help message.
EOF
}

while (($# > 0)); do
  case "$1" in
    --dev)
      dev=true
      ;;
    --refresh-deps)
      refresh_deps=true
      ;;
    --api-base-url)
      shift
      if (($# == 0)); then
        printf '%s\n' "--api-base-url requires a value." >&2
        exit 1
      fi
      api_base_url="$1"
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
  printf '%s\n' "uv is required. Install from https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  printf '%s\n' "Created .env from .env.example - edit if needed."
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

venv_dir=".venv"
venv_python="$venv_dir/bin/python"
venv_cli="$venv_dir/bin/context-engine"
fallback_cli="$venv_dir/bin/context-tui"

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
if [[ ! -x "$venv_cli" && ! -x "$fallback_cli" ]]; then
  # New script entrypoints require reinstall when migrating from old ragcli-only envs.
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

if [[ -z "$api_base_url" ]]; then
  api_port="${API_PORT:-$(read_env_value API_PORT .env)}"
  api_port="${api_port:-8010}"
  api_host="${API_HOST:-$(read_env_value API_HOST .env)}"
  api_host="${api_host:-127.0.0.1}"
  api_base_url="http://${api_host}:$api_port"
fi

if [[ ! -x "$venv_cli" ]]; then
  if [[ -x "$fallback_cli" ]]; then
    venv_cli="$fallback_cli"
  else
    printf '%s\n' "context-engine executable not found. Re-run with --refresh-deps." >&2
    exit 1
  fi
fi

printf '%s\n' "CLI ready."
printf 'API base URL: %s\n' "$api_base_url"
printf '\n'
printf '%s\n' "Example commands:"
printf "  export CONTEXT_ENGINE_API_BASE_URL='%s'\n" "$api_base_url"
printf '  %s --help\n' "$venv_cli"
printf '  %s\n' "$venv_cli"
printf '\n'

export CONTEXT_ENGINE_API_BASE_URL="$api_base_url"
exec "$venv_cli"
