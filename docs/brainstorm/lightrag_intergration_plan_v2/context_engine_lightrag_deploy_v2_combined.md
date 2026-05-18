# 1. Final Architecture Decisions

## 1.1 Final Product Shape

`context_engine` is the single operator-facing application.

Operators should not need to run Easy Deploy LightRAG directly. Instead, Context Engine should expose the useful Easy Deploy capabilities through its own backend API and terminal UI.

`easy-deploy-lightrag` is source material only:

- reuse concepts
- reuse simple algorithms where appropriate
- do not copy its whole app structure
- do not introduce a second CLI, backend, or frontend
- do not vendor LightRAG internals into `app/`

## 1.2 Core Principle

```text
Merge capabilities, not internal complexity.
```

That means Context Engine should gain the capability to create/manage LightRAG domains, but it should not absorb the entire Easy Deploy app or LightRAG internals.

## 1.3 Data Plane vs Control Plane

This split is the key to avoiding redundancy.

### Data Plane: runtime LightRAG use

The existing HTTP-only LightRAG adapter remains the runtime boundary.

```text
User query / upload / graph request
  ↓
Context Engine API
  ↓
RetrievalService / DocumentService / Graph route
  ↓
LightRAGRemoteAdapter
  ↓
HTTP request to selected running LightRAG domain
```

Data-plane responsibilities:

- query/retrieve/answer through LightRAG
- upload forwarding to LightRAG
- status polling from LightRAG
- graph proxy requests
- normalize LightRAG evidence into Context Engine response contracts

### Control Plane: domain deployment and lifecycle

The new module handles deployment/admin operations only.

```text
Admin TUI / Admin API
  ↓
Context Engine LightRAG domain service
  ↓
manifest + generated env + generated compose
  ↓
Docker Compose
  ↓
running LightRAG domain container
```

Control-plane responsibilities:

- create domain
- validate domain ID and port
- create `.data/lightrag/domains/<domain>/...`
- generate domain env files
- update manifest
- generate compose file
- start/stop/recreate containers
- archive/remove domains
- health/status checks

## 1.4 What Must Not Happen

Avoid these entropy traps:

```text
BAD:
- TUI screen calls Docker directly
- TUI screen calls LightRAG directly
- CLI/TUI duplicates backend business logic
- Retrieval adapter starts/stops containers
- Deployment module performs retrieval
- Context Engine imports LightRAG internals
- Easy Deploy repo is copied wholesale
- Root `.env.example` and domain env files become competing sources of truth
- Multiple domain registries exist
- Normal users can mutate domains or indexes
```

## 1.5 Final Architecture

```text
                         ┌──────────────────────────────┐
                         │  Context Engine Terminal UI  │
                         │  cli/launcher.py + cli/tui   │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
                                cli/services/*
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Context Engine API                          │
│                                                                     │
│  Existing runtime routes                                             │
│   ├── /query, /query/retrieve, /query/answer                         │
│   ├── /admin/documents/upload                                        │
│   ├── /graphs, /graph/label/...                                      │
│   └── /lightrag/domains or similar read list for normal users         │
│                                                                     │
│  New admin control routes                                            │
│   └── /admin/lightrag/domains/...                                    │
│                                                                     │
└───────────────┬───────────────────────────────────────┬─────────────┘
                │                                       │
                ▼                                       ▼
     Existing runtime adapter                 New deployment manager
 app/integrations/lightrag_remote_adapter     app/lightrag_deploy/*
                │                                       │
                ▼                                       ▼
     Running LightRAG domain HTTP API          .data + generated compose
```

## 1.6 Final Module Placement

Add a new small module:

```text
app/lightrag_deploy/
  __init__.py
  models.py
  settings.py
  paths.py
  manifest.py
  compose.py
  docker_runner.py
  health.py
  service.py
  errors.py
```

Keep existing runtime integration in:

```text
app/integrations/lightrag_remote_adapter.py
app/integrations/lightrag_domains.py
app/retrieval/lightrag_remote_engine.py
app/api/routes/lightrag.py
```

## 1.7 Why This Is Simple

The system has only one owner for each responsibility:

| Responsibility | Owner |
|---|---|
| Auth/RBAC | Existing Context Engine auth/deps |
| Document registry | Existing Context Engine document model/repository |
| Query/retrieve/answer | Existing Context Engine query/retrieval services |
| Runtime LightRAG HTTP calls | Existing `LightRAGRemoteAdapter` |
| Domain deployment lifecycle | New `app/lightrag_deploy/service.py` |
| TUI presentation | `cli/tui/` screens |
| TUI API calls | `cli/services/` |
| Configuration source of truth | Root `.env.example` + `app/core/config.py` |
| Runtime generated files | `.data/lightrag/...` |


---

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


---

# 3. Backend Module and API Plan

## 3.1 New Backend Module

Add:

```text
app/lightrag_deploy/
  __init__.py
  models.py
  settings.py
  paths.py
  manifest.py
  compose.py
  docker_runner.py
  health.py
  service.py
  errors.py
```

## 3.2 Module Responsibilities

| File | Responsibility |
|---|---|
| `models.py` | Pydantic/domain models: `LightRAGDomain`, `DomainStatus`, requests/responses. |
| `settings.py` | Adapts `app.core.config.Settings` into deployment-specific config. |
| `paths.py` | Resolves `.data/lightrag/...` paths and creates folder structures. |
| `manifest.py` | Atomic read/write of `domains.json`; validation; no Docker calls. |
| `compose.py` | Deterministic compose-file generation from manifest/settings; no subprocess calls. |
| `docker_runner.py` | Small command runner interface for `docker compose`; fakeable in tests. |
| `health.py` | HTTP health checks against running LightRAG domains. |
| `service.py` | Main orchestration use cases: create/list/show/up/down/recreate/remove/status. |
| `errors.py` | Typed errors converted to HTTP responses by route layer. |

## 3.3 Keep Existing Runtime Modules

Do not replace these:

```text
app/integrations/lightrag_remote_adapter.py
app/integrations/lightrag_domains.py
app/retrieval/lightrag_remote_engine.py
app/api/routes/lightrag.py
```

Instead, update `app/integrations/lightrag_domains.py` to read the same generated manifest if needed.

## 3.4 New Route File

Add:

```text
app/api/routes/lightrag_admin.py
```

Mount it in `app/main.py`.

## 3.5 Admin-Only Domain Control APIs

Prefix:

```text
/admin/lightrag/domains
```

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/admin/lightrag/domains` | Admin | List all configured domains with status/health. |
| `POST` | `/admin/lightrag/domains` | Admin | Create/register a new domain. |
| `GET` | `/admin/lightrag/domains/{domain_id}` | Admin | Show one domain, paths, status, health. |
| `POST` | `/admin/lightrag/domains/{domain_id}/up` | Admin | Start domain container. |
| `POST` | `/admin/lightrag/domains/{domain_id}/down` | Admin | Stop domain container. |
| `POST` | `/admin/lightrag/domains/{domain_id}/recreate` | Admin | Recreate domain container. |
| `POST` | `/admin/lightrag/domains/{domain_id}/regenerate` | Admin | Regenerate domain env + compose without starting. |
| `DELETE` | `/admin/lightrag/domains/{domain_id}` | Admin | Archive/remove domain by default. |
| `DELETE` | `/admin/lightrag/domains/{domain_id}?permanent=true` | Admin + config | Permanent delete only if explicitly enabled. |

## 3.6 User-Safe Domain Read API

Normal users need domain list for query selection.

Add a separate read-only route:

```text
GET /lightrag/domains
```

Auth:

```text
authenticated user
```

Response should include only user-safe information:

```json
{
  "domains": [
    {
      "id": "fatigue",
      "display_name": "Fatigue Manuals",
      "base_url": null,
      "is_healthy": true,
      "is_default": false
    }
  ]
}
```

Do not expose:

- env paths
- secrets
- Docker command details
- host file paths if not needed
- container names unless harmless

## 3.7 Request/Response Models

Suggested schemas:

```python
class LightRAGDomainCreateRequest(BaseModel):
    domain_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")
    display_name: str | None = None
    host_port: int | None = Field(default=None, ge=1, le=65535)
    make_default: bool = False

class LightRAGDomainResponse(BaseModel):
    id: str
    display_name: str
    host_port: int
    container_port: int
    base_url: str
    service_name: str
    container_name: str
    status: str
    is_healthy: bool | None = None
    created_at: datetime
    updated_at: datetime

class LightRAGDomainRemoveResponse(BaseModel):
    id: str
    archived: bool
    archive_path: str | None
    permanent: bool
```

## 3.8 Service Methods

`app/lightrag_deploy/service.py` should expose a small class:

```python
class LightRAGDomainService:
    def list_domains(self) -> list[LightRAGDomain]: ...
    def get_domain(self, domain_id: str) -> LightRAGDomain: ...
    def create_domain(self, request: LightRAGDomainCreateRequest) -> LightRAGDomain: ...
    def regenerate(self, domain_id: str | None = None) -> None: ...
    def up(self, domain_id: str) -> LightRAGDomainOperationResult: ...
    def down(self, domain_id: str) -> LightRAGDomainOperationResult: ...
    def recreate(self, domain_id: str) -> LightRAGDomainOperationResult: ...
    def remove(self, domain_id: str, *, permanent: bool = False) -> LightRAGDomainRemoveResponse: ...
    def status(self, domain_id: str) -> LightRAGDomainStatus: ...
```

Keep service methods boring and easy to follow.

## 3.9 Route Layer Rules

Routes should:

- parse request
- enforce `require_admin` or authenticated user
- call `LightRAGDomainService`
- map typed errors to HTTP exceptions
- return schema objects

Routes should not:

- build Docker commands
- write files directly
- know compose syntax
- implement deletion logic
- call LightRAG HTTP runtime APIs directly except through service/health helpers

## 3.10 Config Guard

If `LIGHTRAG_DEPLOY_ENABLED=false`, admin deployment routes should return:

```text
403 or 400: LightRAG deployment is disabled
```

Recommendation:

- Use `400` when feature disabled due config.
- Use `403` when user lacks admin rights.

## 3.11 Audit Logging

Every admin domain operation should write an audit event:

```text
lightrag.domain.created
lightrag.domain.started
lightrag.domain.stopped
lightrag.domain.recreated
lightrag.domain.archived
lightrag.domain.deleted_permanently
lightrag.domain.regenerated
```

Metadata should include:

```json
{
  "domain_id": "fatigue",
  "host_port": 9622,
  "service_name": "lightrag_fatigue"
}
```

## 3.12 System Status Integration

If there is or will be an admin system status endpoint, include:

- deployment feature enabled/disabled
- manifest path exists/readable
- compose file exists
- Docker executable reachable
- Docker socket/daemon reachable
- configured domains count
- unhealthy domains count
- missing path warnings


---

# 4. Terminal UI Integration Plan

## 4.1 Current CLI/TUI Architecture Assumption

Do not design for the older `ragcli` command-tree model.

Use the current terminal UI structure:

```text
cli/
  launcher.py              # terminal UI launcher
  config.py                # optional argparse/settings
  credentials.py           # credential storage
  api_client.py            # HTTP wrapper
  services/                # feature-oriented API call helpers
  tui/                     # Rich TUI screens
  main.py                  # legacy compatibility delegate only
```

## 4.2 TUI Rules

- TUI screens are presentation only.
- TUI screens call `cli/services/*`.
- `cli/services/*` calls Context Engine API through `ApiClient`.
- No Docker calls in TUI screens.
- No direct LightRAG calls in TUI screens.
- No file/env/manifest manipulation in TUI screens.
- `cli/main.py` remains a compatibility delegate to launcher only.

## 4.3 New CLI Service

Add:

```text
cli/services/lightrag_domains.py
```

Suggested class:

```python
class LightRAGDomainService:
    def __init__(self, api_client: ApiClient): ...

    def list_user_domains(self) -> dict: ...
    def list_admin_domains(self) -> dict: ...
    def create_domain(self, payload: dict) -> dict: ...
    def show_domain(self, domain_id: str) -> dict: ...
    def up_domain(self, domain_id: str) -> dict: ...
    def down_domain(self, domain_id: str) -> dict: ...
    def recreate_domain(self, domain_id: str) -> dict: ...
    def regenerate_domain(self, domain_id: str | None = None) -> dict: ...
    def remove_domain(self, domain_id: str, *, permanent: bool = False) -> dict: ...
```

This class only constructs HTTP requests to Context Engine.

## 4.4 Admin TUI Menu

Add a screen flow like:

```text
Admin Menu
  ├── Documents
  ├── Jobs
  ├── Logs
  ├── System Status
  └── LightRAG Domains
        ├── List domains
        ├── Create domain
        ├── Show domain detail
        ├── Start domain
        ├── Stop domain
        ├── Recreate domain
        ├── Regenerate config
        ├── Archive/remove domain
        └── Health/status
```

## 4.5 Normal User Domain Selection

Normal users should be able to select a LightRAG domain for query/upload contexts where applicable.

Suggested user-safe UI:

```text
Query Settings
  ├── Retrieval mode: auto / semantic / navigation / hybrid
  ├── LightRAG domain: [default / fatigue / abaqus / hospital-beds]
  └── Top K: 8
```

The user-facing domain selector must call:

```text
GET /lightrag/domains
```

not the admin endpoint.

## 4.6 Admin Domain List Screen

Example layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ LightRAG Domains                                             │
├─────────────┬────────────┬─────────┬──────────┬──────────────┤
│ Domain      │ Port       │ Status  │ Health   │ Last Updated │
├─────────────┼────────────┼─────────┼──────────┼──────────────┤
│ fatigue     │ 9622       │ running │ healthy  │ 2026-05-18   │
│ abaqus      │ 9623       │ stopped │ unknown  │ 2026-05-18   │
└─────────────┴────────────┴─────────┴──────────┴──────────────┘

Actions: [C]reate  [S]tart  S[t]op  [R]ecreate  [D]etail  [A]rchive  [B]ack
```

## 4.7 Create Domain Screen

Fields:

```text
Domain ID:       fatigue
Display name:    Fatigue Manuals
Host port:       blank for auto
Make default:    no
```

Validation should happen both in TUI and backend, but backend is source of truth.

## 4.8 Remove Domain Screen

Default behavior:

```text
Archive domain data? yes
Permanent delete? no
```

Permanent delete should require a deliberate confirmation phrase, for example:

```text
Type DELETE fatigue to permanently delete this domain.
```

But permanent delete should only be available if:

```env
LIGHTRAG_ALLOW_PERMANENT_DELETE=true
```

## 4.9 Error Display

Map backend errors to clear TUI messages:

| Backend Error | TUI Message |
|---|---|
| Deployment disabled | `LightRAG deployment is disabled. Enable LIGHTRAG_DEPLOY_ENABLED=true.` |
| Docker unavailable | `Docker is not reachable from Context Engine.` |
| Port conflict | `Port 9622 is already used by another domain or process.` |
| Invalid domain ID | `Use lowercase letters, numbers, hyphen, or underscore.` |
| Domain not found | `Domain does not exist.` |
| Permission denied | `Admin access required.` |

## 4.10 Testing TUI

Add tests around:

- service URL/payload construction
- admin screen rendering with fake API response
- user domain selector rendering
- create-domain form validation
- remove-domain confirmation behavior
- error rendering

Do not test real Docker from TUI tests.


---

# 5. Domain Lifecycle and Document Flow

## 5.1 Domain Lifecycle

### Create domain

```text
Admin TUI
  ↓
POST /admin/lightrag/domains
  ↓
LightRAGDomainService.create_domain()
  ↓
validate domain ID
  ↓
choose/validate host port
  ↓
create .data/lightrag/domains/<domain>/ folders
  ↓
generate domain.env
  ↓
update .data/lightrag/domains.json
  ↓
regenerate .data/lightrag/docker-compose.lightrag-domains.yml
  ↓
audit log
  ↓
return domain response
```

### Start domain

```text
POST /admin/lightrag/domains/{domain_id}/up
  ↓
load manifest
  ↓
ensure compose is up to date
  ↓
docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml up -d lightrag_<domain>
  ↓
poll health endpoint
  ↓
audit log
  ↓
return operation result
```

### Stop domain

```text
POST /admin/lightrag/domains/{domain_id}/down
  ↓
docker compose -f ... stop lightrag_<domain>
  ↓
audit log
  ↓
return operation result
```

### Recreate domain

```text
POST /admin/lightrag/domains/{domain_id}/recreate
  ↓
docker compose -f ... up -d --force-recreate lightrag_<domain>
  ↓
poll health
  ↓
audit log
  ↓
return operation result
```

### Archive/remove domain

```text
DELETE /admin/lightrag/domains/{domain_id}
  ↓
stop container if running
  ↓
remove from manifest
  ↓
regenerate compose
  ↓
move .data/lightrag/domains/<domain>/ to .data/lightrag/deleted/<domain>-timestamp/
  ↓
audit log
  ↓
return archive path
```

### Permanent delete

```text
DELETE /admin/lightrag/domains/{domain_id}?permanent=true
```

Allowed only if:

```env
LIGHTRAG_ALLOW_PERMANENT_DELETE=true
```

and the API request explicitly asks for permanent delete.

## 5.2 Domain States

Use simple states:

```text
configured      # manifest/folders/env exist; not necessarily running
starting        # operation in progress if tracked
running         # container appears running and health OK
stopped         # container stopped
unhealthy       # container running but health check fails
archived        # removed from active manifest and moved to deleted/
error           # last operation failed
```

Do not overbuild state machines in v1. Most status can be computed from manifest + Docker status + health check.

## 5.3 One Document Belongs to One Domain

Rule:

```text
A document uploaded to LightRAG domain `fatigue` belongs only to `fatigue`.
```

Do not fan out one document to multiple LightRAG domains in v1.

## 5.4 Upload Flow With Domain Selection

```text
Admin selects domain in TUI upload screen
  ↓
POST /admin/documents/upload with domain_id=fatigue
  ↓
DocumentService saves local mirror file under Context Engine storage
  ↓
Document row records lightrag_domain_id=fatigue
  ↓
DocumentService resolves domain base_url from manifest
  ↓
LightRAGRemoteAdapter.for_domain(fatigue).upload_document(...)
  ↓
Document row stores external document ID / track ID / status
  ↓
return document response
```

## 5.5 Query Flow With Domain Selection

Normal user query:

```text
User selects domain: fatigue
  ↓
POST /query/retrieve or /query/answer with lightrag_domain_id=fatigue
  ↓
RetrievalService validates domain exists and user can read
  ↓
RetrievalRoutingPolicy selects LightRAG for semantic/hybrid/auto if enabled
  ↓
LightRAGRemoteAdapter uses domain-specific base_url/api_key
  ↓
Evidence normalized into Context Engine response
```

## 5.6 Suggested Query Request Extension

Add optional domain field:

```python
class QueryRequest(BaseModel):
    query: str
    mode: RetrievalMode = RetrievalMode.AUTO
    document_ids: list[UUID] | None = None
    lightrag_domain_id: str | None = None
    top_k: int = 8
    include_debug: bool = False
```

Rules:

- If `lightrag_domain_id` is omitted, use default domain.
- If `mode=navigation`, local Context Engine navigation path may ignore LightRAG domain unless document filtering requires it.
- If `document_ids` are provided, ensure those documents belong to the selected domain or return `400`.

## 5.7 Suggested Upload Request Extension

Admin upload should accept domain ID:

```text
POST /admin/documents/upload
multipart/form-data:
  file=<file>
  lightrag_domain_id=fatigue
```

Rules:

- `lightrag_domain_id` is required when `LIGHTRAG_ENABLED=true` and multiple domains exist.
- If omitted and only one/default domain exists, use default.
- If domain is stopped/unhealthy, return clear error before uploading.

## 5.8 Document Metadata

At minimum store in document metadata:

```json
{
  "lightrag": {
    "domain_id": "fatigue",
    "external_document_id": "external-doc-id",
    "track_id": "upload-track-id",
    "status": "indexing",
    "base_url_key": "fatigue"
  }
}
```

If you already have DB columns for external engine/status, prefer columns for frequently queried fields and metadata for provider-specific payload.

## 5.9 Deleting Documents

Document delete should be separate from domain delete.

V1 recommendation:

- Context Engine marks document deleted locally.
- If LightRAG delete-document API is stable, optionally forward delete to selected domain.
- If LightRAG delete API is not stable, document remains in LightRAG until domain rebuild/reindex.
- Document should be hidden from Context Engine query results once local status is deleted.

## 5.10 Status Polling

Use existing LightRAG track status helper if present.

Add later if not already exposed:

```text
POST /admin/documents/{document_id}/refresh-lightrag-status
```

This is lower priority than domain create/list/up/down.


---

# 6. Docker Compose Execution Plan

## 6.1 Goal

Context Engine should manage LightRAG domain containers on the same machine when that reduces operator complexity.

It must support two deployment shapes:

1. Context Engine running on the host.
2. Context Engine running inside Docker.

## 6.2 Recommended v1 Strategy

Use one code path:

```text
LightRAGDomainService
  ↓
ComposeGenerator
  ↓
DockerComposeRunner
  ↓
docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml ...
```

The only difference between host/container mode is how Docker is reachable.

## 6.3 Host Mode

Best for development and simplest operator setup.

```text
Context Engine process runs on host
  ↓
subprocess: docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml up -d lightrag_fatigue
  ↓
Docker daemon starts container
```

Config:

```env
LIGHTRAG_DOCKER_EXECUTION_MODE=host
LIGHTRAG_DOCKER_COMPOSE_BIN=docker compose
```

## 6.4 Docker Mode

Context Engine runs inside a container but controls Docker on the same host.

Simplest implementation:

- mount Docker socket into Context Engine container
- install Docker CLI/Compose plugin in the Context Engine image
- mount `.data/` path consistently

Example compose snippet concept:

```yaml
services:
  api:
    volumes:
      - ./.data:/app/.data
      - /var/run/docker.sock:/var/run/docker.sock
```

Config:

```env
LIGHTRAG_DOCKER_EXECUTION_MODE=socket
LIGHTRAG_DOCKER_COMPOSE_BIN=docker compose
```

Security note: Docker socket access is powerful. This is acceptable only for the stated local/trusted-network deployment assumption. Do not expose this admin API to the internet.

## 6.5 Avoid a Separate Host Agent in v1

Do not add a separate daemon/agent just to run Docker commands unless Docker socket mode becomes unacceptable.

A host agent adds:

- new process
- new API surface
- new auth problem
- new deployment docs
- new failure mode

For a 5–10 user local-network app, Docker CLI/socket is simpler.

## 6.6 Compose File Generation

Generated file:

```text
.data/lightrag/docker-compose.lightrag-domains.yml
```

Header:

```yaml
# Generated by Context Engine. Do not edit by hand.
# Source of truth: root .env + .data/lightrag/domains.json
```

Compose should include one service per domain:

```yaml
services:
  lightrag_fatigue:
    image: ${LIGHTRAG_IMAGE}
    container_name: context_engine_lightrag_fatigue
    env_file:
      - .data/lightrag/domains/fatigue/domain.env
    ports:
      - "127.0.0.1:9622:9621"
    volumes:
      - .data/lightrag/domains/fatigue/inputs:/app/data/inputs
      - .data/lightrag/domains/fatigue/rag_storage:/app/data/rag_storage
      - .data/lightrag/domains/fatigue/artifacts:/app/data/artifacts
    networks:
      - context_engine_lightrag

networks:
  context_engine_lightrag:
    name: context_engine_lightrag
```

## 6.7 Shared Services

Keep shared service strategy configurable.

V1 simplest options:

### Option A: Each domain uses LightRAG image defaults

Lowest coordination. Good for first slice if LightRAG image supports local file storage defaults.

### Option B: Domains use shared Postgres/Redis/Neo4j from Context Engine compose

More operationally consistent but needs careful env settings.

Use `.env.example` to document both, but implement one default path first.

Recommended v1:

- Use domain-local storage where possible.
- Allow shared service URLs through env settings.
- Do not force Neo4j/Postgres/Redis complexity unless LightRAG requires it.

## 6.8 Docker Runner Interface

Create fakeable runner:

```python
class DockerComposeRunner(Protocol):
    def up(self, service_name: str) -> CommandResult: ...
    def down(self, service_name: str) -> CommandResult: ...
    def stop(self, service_name: str) -> CommandResult: ...
    def recreate(self, service_name: str) -> CommandResult: ...
    def ps(self) -> CommandResult: ...
```

Default implementation:

```python
class SubprocessDockerComposeRunner:
    def __init__(self, compose_file: Path, compose_bin: str, timeout_seconds: int): ...
```

Tests should use:

```python
class FakeDockerComposeRunner:
    ...
```

## 6.9 Port Rules

- Domain host port must be unique in manifest.
- Domain host port must not equal Context Engine API/client ports.
- If port omitted, choose next available starting at `LIGHTRAG_DEFAULT_PORT_START`.
- Optional: check OS port availability before creating domain.

## 6.10 Network Rules

For host-run Context Engine:

```text
base_url = http://127.0.0.1:<host_port>
```

For Docker-run Context Engine:

Two possibilities:

1. If API container uses host networking or can reach host published ports, keep `http://host.docker.internal:<port>` where supported.
2. If API container joins `context_engine_lightrag` network, use service DNS:

```text
http://lightrag_fatigue:9621
```

Recommendation:

Store both:

```json
{
  "host_base_url": "http://127.0.0.1:9622",
  "container_base_url": "http://lightrag_fatigue:9621"
}
```

Then select at runtime based on:

```env
LIGHTRAG_DOCKER_EXECUTION_MODE=host|socket
```

## 6.11 Do Not Mutate Root Docker Compose in v1

Do not rewrite the root `docker-compose.yml` from the app.

Generate a separate LightRAG compose file:

```text
.data/lightrag/docker-compose.lightrag-domains.yml
```

This keeps generated deployment state separate from source-controlled infrastructure.


---

# 7. TDD and Quality Plan

## 7.1 Testing Principle

Test public behavior, not implementation details.

Do not require live Docker or live LightRAG for ordinary tests.

Use:

- temp directories for `.data`
- fake manifest paths
- fake Docker runner
- mocked HTTP health checks
- API TestClient for route behavior
- fake ApiClient for TUI service tests

## 7.2 Test Slices

### Slice 1: Settings and paths

Tests:

- `.env.example` contains all runtime and deployment LightRAG settings.
- Settings parse deployment fields.
- Path resolver creates domain paths under `.data/lightrag/domains/<domain>`.
- Invalid domain IDs fail.

Files:

```text
tests/test_lightrag_deploy_settings.py
tests/test_lightrag_deploy_paths.py
```

### Slice 2: Manifest read/write

Tests:

- Missing manifest returns empty domain list.
- Create domain writes deterministic manifest.
- Duplicate domain ID fails.
- Duplicate port fails.
- Manifest writes atomically.

File:

```text
tests/test_lightrag_deploy_manifest.py
```

### Slice 3: Domain storage creation

Tests:

- Create domain creates `inputs`, `rag_storage`, `artifacts`, `logs`.
- Generated `domain.env` includes header warning.
- Generated env is deterministic.

File:

```text
tests/test_lightrag_deploy_domain_files.py
```

### Slice 4: Compose generation

Tests:

- Compose file includes one service per domain.
- Compose output is deterministic.
- Compose includes correct ports and volumes.
- Compose header says generated/do-not-edit.

File:

```text
tests/test_lightrag_deploy_compose.py
```

### Slice 5: Domain service create/list/show/remove

Tests:

- `create_domain()` returns expected model.
- `list_domains()` returns configured domains.
- `remove(permanent=False)` archives domain directory.
- `remove(permanent=True)` fails unless config allows it.
- Archive path includes timestamp.

File:

```text
tests/test_lightrag_deploy_service.py
```

### Slice 6: Docker operations with fake runner

Tests:

- `up()` calls fake runner with correct service name.
- `down()` calls fake runner.
- `recreate()` calls fake runner.
- Docker error maps to typed service error.
- Health polling can be mocked.

File:

```text
tests/test_lightrag_deploy_docker_runner.py
```

### Slice 7: Admin API routes

Tests:

- Normal user cannot create/up/down/remove domains.
- Admin can create domain.
- Admin can list domains.
- Deployment disabled returns stable error.
- Permanent delete requires explicit config.

File:

```text
tests/test_lightrag_deploy_api.py
```

### Slice 8: User-safe domain list

Tests:

- Authenticated users can list domain choices.
- Response does not expose secrets or host filesystem paths.
- Unauthenticated user gets auth error.

File:

```text
tests/test_lightrag_domains_user_api.py
```

### Slice 9: Upload domain ownership

Tests:

- Admin upload with `lightrag_domain_id` stores local document mirror with domain metadata.
- Upload to missing domain fails.
- Upload to unhealthy/stopped domain fails clearly.
- If document IDs are filtered during query, selected documents must belong to selected domain.

File:

```text
tests/test_lightrag_domain_document_ownership.py
```

### Slice 10: TUI service and screens

Tests:

- `cli/services/lightrag_domains.py` calls correct API paths.
- Admin domain list screen renders fake domain table.
- User query domain selector renders only safe fields.
- TUI does not import Docker runner or deployment service.

Files:

```text
tests/test_cli_services_lightrag_domains.py
tests/test_cli_tui_lightrag_domains.py
```

## 7.3 No-Live-Dependency Rule

Default test suite must not require:

- Docker daemon
- live LightRAG service
- Neo4j
- real Redis unless existing test mode already requires it
- external network

Add optional integration tests later under a marker:

```bash
pytest -m lightrag_live
pytest -m docker_integration
```

## 7.4 Regression Behaviors to Preserve

Preserve existing behavior:

- `LIGHTRAG_ENABLED=false` keeps local upload/query path active.
- Normal users cannot upload.
- Existing graph proxy routes still work.
- Runtime adapter still normalizes evidence.
- Local navigation stays local even when LightRAG is enabled, unless a deliberate later change is made.
- CLI/TUI never calls LightRAG directly.

## 7.5 Quality Gates

Before merge:

```bash
pytest
python -m compileall app cli
```

If using generated compose tests:

```bash
docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml config
```

Run the compose validation manually or in an optional integration job, not in default unit tests.

## 7.6 Code Review Checklist

- Is there one owner for each responsibility?
- Are all settings in root `.env.example`?
- Are generated files clearly marked generated?
- Does the TUI call only `cli/services/`?
- Does `cli/services/` call only Context Engine API?
- Are Docker calls hidden behind `docker_runner.py`?
- Are runtime LightRAG HTTP calls still behind `LightRAGRemoteAdapter`?
- Can Context Engine start with `LIGHTRAG_DEPLOY_ENABLED=false`?
- Can tests run without Docker/LightRAG?
- Is archive the default removal behavior?


---

# 8. Coding Agent Implementation Prompt

Use this prompt with a coding agent.

```markdown
# Task: Add LightRAG Domain Deployment Control to Context Engine

You are a senior software engineer. Implement clean, modular, junior-readable code.

## Goal

Add Easy Deploy LightRAG-style domain deployment capabilities into `context_engine` as a small admin-control feature.

`context_engine` must remain the only operator-facing app. Do not copy `easy-deploy-lightrag` wholesale. Use it only as source material for simple domain deployment behavior.

## Locked Product Decisions

- Context Engine is the only app operators use.
- Easy Deploy LightRAG is source material only.
- Runtime LightRAG calls remain HTTP-only through `LightRAGRemoteAdapter`.
- Context Engine must not import LightRAG Python internals.
- Each domain is a separate LightRAG container.
- One document belongs to exactly one LightRAG domain.
- All LightRAG runtime and deployment settings must be declared in root `.env.example`.
- Generated per-domain env files are outputs only and should not be hand-edited.
- Rich TUI exposes LightRAG domain deployment under an admin screen.
- TUI screens call `cli/services/`; Docker/domain lifecycle logic stays out of screens.
- Deployment routes are admin-only.
- Normal users can list available domains for query selection.
- Docker Compose may be used on the same machine to reduce operator complexity.
- Context Engine must support host-run and Docker-run modes.
- Removing a domain archives by default.
- Permanent delete requires explicit API parameter and config allowance.
- Domain data lives under `.data/lightrag/domains/<domain>/`.
- All storage should live under `.data/` where practical.

## Architecture Rule

Use a control-plane/data-plane split.

Data plane already exists:

```text
Context Engine API
  -> RetrievalService / DocumentService / graph routes
  -> LightRAGRemoteAdapter
  -> running LightRAG domain HTTP API
```

Add only the control plane:

```text
Admin API / TUI
  -> app/lightrag_deploy/service.py
  -> manifest/env/compose generation
  -> Docker Compose runner
  -> running LightRAG domain containers
```

## Do Not Do

- Do not create a second app inside Context Engine.
- Do not put Docker logic in TUI screens.
- Do not make CLI/TUI call LightRAG directly.
- Do not make runtime adapter manage Docker.
- Do not make deployment manager perform retrieval.
- Do not copy Easy Deploy source wholesale.
- Do not mutate root `docker-compose.yml` from the app.
- Do not require LightRAG deployment mode for normal tests.
- Do not allow normal users to create/delete/start/stop domains.

## Add Backend Module

Create:

```text
app/lightrag_deploy/
  __init__.py
  models.py
  settings.py
  paths.py
  manifest.py
  compose.py
  docker_runner.py
  health.py
  service.py
  errors.py
```

Responsibilities:

- `models.py`: Pydantic/domain models.
- `settings.py`: convert app settings into deployment config.
- `paths.py`: resolve `.data/lightrag/...` paths.
- `manifest.py`: read/write `domains.json` atomically.
- `compose.py`: deterministic generated compose file.
- `docker_runner.py`: fakeable Docker Compose subprocess wrapper.
- `health.py`: HTTP health checks.
- `service.py`: create/list/show/up/down/recreate/remove/regenerate.
- `errors.py`: typed errors.

## Add Settings

Update `app/core/config.py` and `.env.example`.

Add runtime section if missing:

```env
LIGHTRAG_ENABLED=false
LIGHTRAG_BASE_URL=http://localhost:9621
LIGHTRAG_API_KEY=
LIGHTRAG_DOMAIN=default
LIGHTRAG_DOMAIN_MANIFEST=.data/lightrag/domains.json
LIGHTRAG_TIMEOUT_SECONDS=10
```

Add deployment section:

```env
LIGHTRAG_DEPLOY_ENABLED=false
LIGHTRAG_DEPLOY_ROOT=.data/lightrag
LIGHTRAG_DOMAINS_ROOT=.data/lightrag/domains
LIGHTRAG_DOMAINS_MANIFEST=.data/lightrag/domains.json
LIGHTRAG_COMPOSE_FILE=.data/lightrag/docker-compose.lightrag-domains.yml
LIGHTRAG_DELETED_ROOT=.data/lightrag/deleted
LIGHTRAG_DEFAULT_PORT_START=9621
LIGHTRAG_DEFAULT_CONTAINER_PORT=9621
LIGHTRAG_DOCKER_NETWORK=context_engine_lightrag
LIGHTRAG_DOMAIN_ENV_FILENAME=domain.env
LIGHTRAG_IMAGE=ghcr.io/hkuds/lightrag:latest
LIGHTRAG_DOCKERFILE=
LIGHTRAG_BUILD_CONTEXT=
LIGHTRAG_POSTGRES_URL=
LIGHTRAG_REDIS_URL=
LIGHTRAG_NEO4J_URI=
LIGHTRAG_NEO4J_USERNAME=
LIGHTRAG_NEO4J_PASSWORD=
LIGHTRAG_ARCHIVE_DELETED_DOMAINS=true
LIGHTRAG_ALLOW_PERMANENT_DELETE=false
LIGHTRAG_DOCKER_EXECUTION_MODE=host
LIGHTRAG_DOCKER_COMPOSE_BIN=docker compose
LIGHTRAG_DOCKER_TIMEOUT_SECONDS=120
```

## Add API Routes

Create `app/api/routes/lightrag_admin.py`.

Admin-only routes:

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
```

User-safe route:

```text
GET /lightrag/domains
```

Admin routes must use `require_admin`. User-safe route must require authenticated user only.

## Add TUI Integration

Use current CLI/TUI architecture:

```text
cli/launcher.py
cli/config.py
cli/credentials.py
cli/api_client.py
cli/services/
cli/tui/
cli/main.py  # compatibility delegate only
```

Add:

```text
cli/services/lightrag_domains.py
cli/tui/screens/lightrag_domains.py
```

Rules:

- TUI screens call only service methods.
- Service methods call only Context Engine API through `ApiClient`.
- No Docker imports in TUI.
- No direct LightRAG HTTP calls in TUI.

## Storage Layout

Use:

```text
.data/lightrag/
  domains.json
  docker-compose.lightrag-domains.yml
  domains/
    <domain>/
      domain.env
      inputs/
      rag_storage/
      artifacts/
      logs/
  deleted/
    <domain>-<timestamp>/
```

## Document Ownership

When LightRAG is enabled, admin upload should take `lightrag_domain_id`.

A document belongs to exactly one domain. Store domain/external IDs in document metadata or columns.

Reject query requests where selected `document_ids` do not belong to the selected `lightrag_domain_id`.

## Docker Strategy

Generate a separate compose file:

```text
.data/lightrag/docker-compose.lightrag-domains.yml
```

Do not modify root `docker-compose.yml` from the app.

Implement a fakeable runner:

```python
class DockerComposeRunner(Protocol):
    def up(self, service_name: str) -> CommandResult: ...
    def stop(self, service_name: str) -> CommandResult: ...
    def recreate(self, service_name: str) -> CommandResult: ...
    def ps(self) -> CommandResult: ...
```

Default implementation uses `subprocess.run` with list args, timeouts, and captured output.

## Testing

Add tests without requiring Docker or live LightRAG:

- settings/env coverage
- domain ID validation
- port conflict detection
- manifest read/write
- domain path creation
- generated env files
- generated compose file
- service create/list/remove/archive
- fake Docker runner up/down/recreate
- admin API auth guard
- user-safe domain list does not expose secrets/paths
- upload with one-domain ownership
- CLI service calls
- TUI rendering with fake API data

## Acceptance Criteria

Implementation is complete when:

1. Context Engine starts normally with `LIGHTRAG_DEPLOY_ENABLED=false`.
2. Root `.env.example` documents all LightRAG runtime and deployment settings.
3. Admin can create/list/show/start/stop/recreate/archive LightRAG domains through Context Engine API.
4. TUI exposes admin LightRAG domain management screens.
5. Normal users can list/select available LightRAG domains for query selection.
6. One uploaded document belongs to one LightRAG domain.
7. Domain storage is under `.data/lightrag/domains/<domain>/`.
8. Generated files are deterministic and marked generated.
9. Permanent delete is disabled by default and requires explicit opt-in.
10. Existing runtime `LightRAGRemoteAdapter` remains the only path for query/upload/graph HTTP traffic.
11. Tests run without Docker or live LightRAG.
12. Code stays small, modular, and junior-readable.
```
