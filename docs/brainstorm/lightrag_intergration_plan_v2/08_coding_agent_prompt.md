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
