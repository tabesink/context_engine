# 2. Single Source `.env.example` and Storage Plan

## 2.1 Rule

Root `.env.example` is the single source of truth for all configurable LightRAG runtime and deployment settings.

Generated per-domain env files are outputs only.

Developers and operators should not hand-edit:

```text
.data/lightrag/domains/<domain>/domain.env
```

If a generated env file is wrong, fix the source setting or manifest and regenerate it.

## 2.2 Settings Categories

Add two clearly separated sections to `.env.example`.

### Runtime LightRAG settings

These already describe how Context Engine talks to a running LightRAG service.

```env
# ---------------------------------------------------------------------
# LightRAG runtime integration
# ---------------------------------------------------------------------
# Enables Context Engine to use running LightRAG services for semantic
# retrieval, upload forwarding, and graph proxy routes.
LIGHTRAG_ENABLED=false
LIGHTRAG_BASE_URL=http://localhost:9621
LIGHTRAG_API_KEY=
LIGHTRAG_DOMAIN=default
LIGHTRAG_DOMAIN_MANIFEST=.data/lightrag/domains.json
LIGHTRAG_TIMEOUT_SECONDS=10
```

### Deployment/control settings

These describe how Context Engine creates/manages LightRAG domain containers.

```env
# ---------------------------------------------------------------------
# LightRAG domain deployment control
# ---------------------------------------------------------------------
# Enables admin-only domain create/up/down/recreate/remove APIs.
LIGHTRAG_DEPLOY_ENABLED=false

# All generated LightRAG deployment state lives under .data by default.
LIGHTRAG_DEPLOY_ROOT=.data/lightrag
LIGHTRAG_DOMAINS_ROOT=.data/lightrag/domains
LIGHTRAG_DOMAINS_MANIFEST=.data/lightrag/domains.json
LIGHTRAG_COMPOSE_FILE=.data/lightrag/docker-compose.lightrag-domains.yml
LIGHTRAG_DELETED_ROOT=.data/lightrag/deleted

# Port/domain defaults.
LIGHTRAG_DEFAULT_PORT_START=9621
LIGHTRAG_DEFAULT_CONTAINER_PORT=9621
LIGHTRAG_DOCKER_NETWORK=context_engine_lightrag
LIGHTRAG_DOMAIN_ENV_FILENAME=domain.env

# Image/build strategy.
# Start with image-based deployment for simplicity. Build support can be added later.
LIGHTRAG_IMAGE=ghcr.io/hkuds/lightrag:latest
LIGHTRAG_DOCKERFILE=
LIGHTRAG_BUILD_CONTEXT=

# Runtime shared services. Keep these blank if a LightRAG image uses file-local defaults.
LIGHTRAG_POSTGRES_URL=
LIGHTRAG_REDIS_URL=
LIGHTRAG_NEO4J_URI=
LIGHTRAG_NEO4J_USERNAME=
LIGHTRAG_NEO4J_PASSWORD=

# Safety behavior.
LIGHTRAG_ARCHIVE_DELETED_DOMAINS=true
LIGHTRAG_ALLOW_PERMANENT_DELETE=false

# Docker execution mode.
# host: Context Engine runs on host and calls docker compose directly.
# socket: Context Engine runs in a container with Docker socket mounted.
LIGHTRAG_DOCKER_EXECUTION_MODE=host
LIGHTRAG_DOCKER_COMPOSE_BIN=docker compose
LIGHTRAG_DOCKER_TIMEOUT_SECONDS=120
```

## 2.3 Settings Ownership in Code

Add fields to `app/core/config.py`.

Suggested Pydantic fields:

```python
# runtime
lightrag_enabled: bool = False
lightrag_base_url: str = "http://localhost:9621"
lightrag_api_key: str | None = None
lightrag_domain: str = "default"
lightrag_domain_manifest: str | None = ".data/lightrag/domains.json"
lightrag_timeout_seconds: float = 10.0

# deployment
lightrag_deploy_enabled: bool = False
lightrag_deploy_root: str = ".data/lightrag"
lightrag_domains_root: str = ".data/lightrag/domains"
lightrag_domains_manifest: str = ".data/lightrag/domains.json"
lightrag_compose_file: str = ".data/lightrag/docker-compose.lightrag-domains.yml"
lightrag_deleted_root: str = ".data/lightrag/deleted"
lightrag_default_port_start: int = 9621
lightrag_default_container_port: int = 9621
lightrag_docker_network: str = "context_engine_lightrag"
lightrag_domain_env_filename: str = "domain.env"
lightrag_image: str = "ghcr.io/hkuds/lightrag:latest"
lightrag_dockerfile: str | None = None
lightrag_build_context: str | None = None
lightrag_postgres_url: str | None = None
lightrag_redis_url: str | None = None
lightrag_neo4j_uri: str | None = None
lightrag_neo4j_username: str | None = None
lightrag_neo4j_password: str | None = None
lightrag_archive_deleted_domains: bool = True
lightrag_allow_permanent_delete: bool = False
lightrag_docker_execution_mode: str = "host"
lightrag_docker_compose_bin: str = "docker compose"
lightrag_docker_timeout_seconds: int = 120
```

## 2.4 Storage Layout

Use one `.data` tree for local runtime state.

```text
.data/
  context_engine.db                         # if SQLite/local mode
  uploads/                                  # current uploaded file storage, if used

  lightrag/
    domains.json                            # generated/managed manifest
    docker-compose.lightrag-domains.yml     # generated compose file

    domains/
      fatigue/
        domain.env                          # generated output
        inputs/                             # source files mirrored/uploaded to this domain
        rag_storage/                        # LightRAG domain storage
        artifacts/                          # parsed/chunked/artifact output if supported
        logs/                               # optional domain logs

      abaqus/
        domain.env
        inputs/
        rag_storage/
        artifacts/
        logs/

    deleted/
      fatigue-2026-05-18-143000/
        domain.env
        inputs/
        rag_storage/
        artifacts/
        logs/
```

## 2.5 Manifest Shape

Use a single manifest at:

```text
.data/lightrag/domains.json
```

Suggested schema:

```json
{
  "version": 1,
  "domains": [
    {
      "id": "fatigue",
      "display_name": "Fatigue Manuals",
      "host": "127.0.0.1",
      "host_port": 9622,
      "container_port": 9621,
      "base_url": "http://127.0.0.1:9622",
      "container_name": "context_engine_lightrag_fatigue",
      "service_name": "lightrag_fatigue",
      "status": "configured",
      "paths": {
        "root": ".data/lightrag/domains/fatigue",
        "env_file": ".data/lightrag/domains/fatigue/domain.env",
        "inputs": ".data/lightrag/domains/fatigue/inputs",
        "rag_storage": ".data/lightrag/domains/fatigue/rag_storage",
        "artifacts": ".data/lightrag/domains/fatigue/artifacts",
        "logs": ".data/lightrag/domains/fatigue/logs"
      },
      "created_at": "2026-05-18T14:30:00Z",
      "updated_at": "2026-05-18T14:30:00Z"
    }
  ]
}
```

## 2.6 Document Ownership Rule

One uploaded document belongs to exactly one LightRAG domain.

Extend document metadata or table fields with:

```text
lightrag_domain_id
lightrag_external_document_id
lightrag_track_id
lightrag_status
lightrag_error
```

Do not use multiple-domain upload in v1. It adds complexity around duplicate external document IDs, status polling, deletion, and reindexing.

## 2.7 Generated Env File Rule

Domain env files should be deterministic and generated by code.

Example generated file header:

```env
# Generated by Context Engine. Do not edit by hand.
# Source of truth: root .env + .data/lightrag/domains.json
# Domain: fatigue

WORKSPACE=fatigue
HOST=0.0.0.0
PORT=9621
INPUT_DIR=/app/data/inputs
WORKING_DIR=/app/data/rag_storage
ARTIFACTS_DIR=/app/data/artifacts
```

## 2.8 Storage Safety Rules

- Archive by default.
- Permanent delete requires explicit API parameter and config allowance.
- Never delete `.data/lightrag/domains/<domain>` silently.
- Do not delete shared service data through domain removal.
- Do not put secrets into source-controlled files.
- Do not require manual edits inside generated `.data` files.
