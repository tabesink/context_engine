# 3. CLI and Deployment Surface

## 3.1 CLI Overview

Primary CLI file: `cli/main.py`  
Interactive chat file: `cli/chat.py`  
Python script entry point in `pyproject.toml`: `lightrag-cli = "cli.main:main"`

The CLI is a Typer/Rich application that manages local LightRAG domain deployments. It writes runtime env files, manages `data/domains.json`, generates `docker-compose.domains.yml`, and runs Docker Compose commands.

## 3.2 CLI Command Map

| Command | Function / Area | Purpose | Calls Docker? | Writes Files? | Notes |
|---|---|---|---:|---:|---|
| `lightrag-cli` with no args | Typer callback | Opens the TUI menu. | Indirect | Indirect | Uses Rich menu UI. |
| `setup` | `setup()` | Guided multi-domain setup. | Optional | Yes | Defaults include domains like `abaqus`, `lsdyna`, `fatigue`, `designlife`. |
| `tui` | `tui()` | Interactive menu for setup/domain/status operations. | Yes | Yes | Menu options call other helpers/commands. |
| `chat` | `chat_command()` imported from `cli.chat` | Starts interactive chat against a domain. | No direct evidence | Unknown | Needs local inspection of `cli/chat.py` for full behavior. |
| `domain add` | `domain_add()` / `_add_domain()` | Adds a domain, creates folders/env, updates compose. | No | Yes | Validates domain id and port. |
| `domain list` | `domain_list()` | Lists configured domains. | No | Reads | Reads manifest. |
| `domain up` | `domain_up()` | Starts all services or selected domain. | Yes | Maybe | Uses Compose. |
| `domain down` | `domain_down()` | Stops all services or selected domain. | Yes | No | Uses Compose. |
| `domain remove` | `domain_remove()` / `_remove_domain()` | Stops and archives/removes domain. | Yes | Yes | Potentially destructive. Archives domain folder under `_deleted`. |
| `domain recreate` | `domain_recreate()` | Recreates a domain service/container. | Yes | Maybe | Used after env/image/config changes. |
| `domain status` | `domain_status()` | Shows configured/running/health status. | Yes | Reads | Uses Docker and health checks. |
| `domain regen` | `domain_regen()` / `_write_compose()` | Regenerates compose file from manifest. | No | Yes | Useful when manifest/env changed. |

## 3.3 Important CLI Helper Functions

| Function | File | Purpose |
|---|---|---|
| `_ensure_runtime_files()` | `cli/main.py` | Creates `data/`, `data/config`, `data/domains`, secret env files, redis config, manifest. |
| `_write_domain_env()` | `cli/main.py` | Creates per-domain folders and `.env` with port/workspace/storage paths. |
| `_compose_header()` | `cli/main.py` | Defines shared PostgreSQL, Redis, and Neo4j Compose services. |
| `_compose_domain()` | `cli/main.py` | Defines a LightRAG domain service for Docker Compose. |
| `_write_compose()` | `cli/main.py` | Regenerates `docker-compose.domains.yml`. |
| `_add_domain()` | `cli/main.py` | Validates and creates a domain definition. |
| `_remove_domain()` | `cli/main.py` | Stops service, archives/removes domain folder, updates manifest and compose. |
| `_run_compose()` | `cli/main.py` | Runs Docker Compose subprocesses. |
| `_health_ok()` / `_poll_health()` | `cli/main.py` | Checks LightRAG health endpoints. |

## 3.4 Deployment Runtime Model

The repo uses two deployment layers:

1. **Committed Compose file**: `docker-compose.domains.yml`
2. **Generated Compose behavior**: `cli/main.py` can regenerate the Compose file based on domain manifest entries.

Main services in `docker-compose.domains.yml`:

| Service | Image / Build | Purpose | Persistence |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | KV/vector/doc-status storage backend for LightRAG. | `./data/postgres` |
| `redis` | `redis:7-alpine` | Redis cache/storage layer for LightRAG. | `./data/redis` |
| `neo4j` | `neo4j:5-community` | Graph storage backend. | `./data/neo4j/data`, `logs`, `import`, `plugins` |
| `lightrag_<domain>` | Build from `Dockerfile.lightrag-local` | Per-domain LightRAG API/runtime. | `./data/domains/<domain>/...` |

Example committed domain service observed:

| Service | Domain | Host Port | Container Port | Workspace |
|---|---|---:|---:|---|
| `lightrag_fatigue` | `fatigue` | `127.0.0.1:9622` | `9622` | `fatigue` |

## 3.5 Dockerfile Behavior

File: `Dockerfile.lightrag-local`

Key behavior:

1. Uses upstream LightRAG image: `ghcr.io/hkuds/lightrag:latest`.
2. Installs extra Python/system dependencies, including `docling`, `pyuca`, `libxcb1`, `libgl1`, `libglib2.0-0`.
3. Copies local `src/lightrag` into `/app/lightrag`, overriding/extending the LightRAG code in the image.

Implication: this repo is not only orchestrating LightRAG; it also injects a local customized LightRAG implementation into the runtime image.

## 3.6 Configuration Files and Env Vars

### Top-level `.env.example`

Observed variables include:

| Variable | Purpose | Notes |
|---|---|---|
| `BACKEND_HOST` | Backend bind host. | Example `127.0.0.1`. |
| `BACKEND_PORT` | Backend port. | Example `8088`. |
| `CLIENT_HOST` | Client bind host. | Example `127.0.0.1`. |
| `CLIENT_PORT` | Client port. | Example `3007`. |
| `BACKEND_ENVIRONMENT` | Backend environment. | Example `local`. |
| `BACKEND_DATABASE_URL` | Backend SQLite URL. | Example uses `sqlite:///data/backend/backend.sqlite3`. See mismatch note below. |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins. | Example `http://127.0.0.1:3007`. |
| `BACKEND_ADMIN_USERNAME` | Bootstrap admin username. | Example `admin`. |
| `BACKEND_ADMIN_PASSWORD` | Bootstrap admin password. | Example `admin123`; should be changed. |
| `BACKEND_JWT_SECRET` | JWT signing secret. | Example `change-me-local-dev-secret`. |
| `BACKEND_AUTH_COOKIE_NAME` | Auth cookie name. | Example `lightrag_session`. |
| `BACKEND_AUTH_COOKIE_SECURE` | Secure cookie toggle. | Should be true behind HTTPS. |
| `BACKEND_LIGHTRAG_BASE_URL` | Default LightRAG server base URL. | Example `http://127.0.0.1:9621`. |
| `BACKEND_LLM_BASE_URL` | LLM provider base URL. | Example local Ollama. |
| `BACKEND_LLM_MODEL` | LLM model. | Example `qwen2.5:14b`. |
| `NEXT_PUBLIC_API_PORT` | Client API port hint. | Example `8088`. |

### Backend Settings Defaults

File: `src/server/config/settings.py`

Important defaults:

| Setting | Default |
|---|---|
| `database_url` | `sqlite:///data/server/server.sqlite3` |
| `cors_origins` | `("http://127.0.0.1:3007",)` |
| `admin_username` | `admin` |
| `admin_password` | `admin123` |
| `jwt_secret` | `change-me-local-dev-secret` |
| `auth_cookie_name` | `lightrag_session` |
| `lightrag_base_url` | `http://127.0.0.1:9621` |
| `domains_manifest_path` | `PROJECT_ROOT/data/domains.json` |
| `chat_rate_limit_per_minute` | `60` |

### Important Config Mismatch

`.env.example` uses:

```text
BACKEND_DATABASE_URL=sqlite:///data/backend/backend.sqlite3
```

`src/server/config/settings.py` defaults to:

```text
sqlite:///data/server/server.sqlite3
```

This is likely either intentional override behavior or stale naming. A coding agent should not change this blindly; first decide which path is canonical.

## 3.7 Scripts

Observed script files:

| Script | Status From Current Review |
|---|---|
| `scripts/deploy_backend_client.sh` | Present. Raw content was not successfully reviewed. |
| `scripts/deploy_server_client.sh` | Present. Raw content was not successfully reviewed. |
| `scripts/deploy_wizard.sh` | Present. Raw content was not successfully reviewed. |

Before changing deployment behavior, inspect these scripts locally and compare them against `cli/main.py` and `docker-compose.domains.yml`.

## 3.8 Deployment Assumptions

| Assumption | Evidence / Reasoning |
|---|---|
| Local machine deployment | Bound ports such as `127.0.0.1:9622:9622`; env defaults use localhost. |
| Docker available | CLI uses Docker Compose and Docker status helpers. |
| Shared storage services | PostgreSQL, Redis, Neo4j are shared services across domains. |
| Per-domain isolation | Domain services use per-domain workspaces and per-domain folders. |
| Local LLM/embedding provider by default | Base env defaults point to Ollama-style URLs/models. |
| Domain manifest controls UI/API discovery | Backend `discover_domains()` reads `data/domains.json` and health-checks domains. |
