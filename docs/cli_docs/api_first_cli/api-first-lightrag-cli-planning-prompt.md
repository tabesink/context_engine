# Coding Agent Planning Prompt: Future API-First LightRAG Deployment + CLI + Frontend

## Purpose

Use this prompt for future deployment/domain-management planning. The task is **planning only**. Do not implement code yet.

The current codebase already supports remote LightRAG retrieval, admin upload forwarding, and graph proxy reads through the FastAPI backend and `ragcli`. The future goal is to add LightRAG knowledge-base/domain deployment, status, deletion, and selected `easy-deploy-lightrag` lifecycle capabilities through the **FastAPI backend first**, then mirror those routes in `ragcli`.

This is important because `ragcli` is not a separate local operator tool. In this project, every real `ragcli` command mirrors an API route. Therefore, the same capabilities must also be usable later from an admin frontend.

---

## Role

You are a senior software architect and coding agent.

Your job is to inspect the codebase and produce a lean, junior-developer-friendly implementation plan.

Design future deployment work so that:

- `context_engine` remains the multi-user application/control plane.
- LightRAG remains the independently deployed retrieval/index/graph engine.
- `ragcli` continues to mirror backend API routes.
- A future admin frontend can call the exact same backend routes.
- Deployment and deletion actions are protected by backend admin authorization.
- The codebase stays simple, modular, and easy to follow.

---

## Repositories To Inspect

### 1. Main repo

```text
https://github.com/tabesink/context_engine.git
```

Inspect at minimum:

```text
app/main.py
app/core/config.py
app/api/deps.py
app/api/routes/
app/services/
app/integrations/
app/storage/
cli/
docs/cli_docs/
external/lightrag/
scripts/
tests/
```

### 2. Reference deployment repo

```text
https://github.com/tabesink/easy-deploy-lightrag.git
```

Inspect at minimum:

```text
cli/main.py
deploy-wizard.sh
scripts/deploy_wizard.sh
docker-compose.domains.yml
Dockerfile.lightrag-local
data/domains.json
data/base.env
data/domains/
```

Focus on existing domain/deployment lifecycle behavior:

- setup / wizard
- domain add
- domain list
- domain up
- domain down
- domain remove/delete
- domain recreate
- domain status
- domain regen
- generated env files
- generated compose files
- domain manifest
- health checks
- Docker/process orchestration
- archive/delete behavior

---

## Core Correction To Previous Plan

Do **not** design `ragcli lightrag ...` as a local-only operator command surface.

In this codebase, `ragcli` commands should be mirrors of FastAPI routes.

Therefore, design the feature as:

```text
Admin frontend
      \
       -> context_engine FastAPI admin deployment routes
      /
ragcli
```

The backend owns the behavior. The CLI only calls the backend.

---

## Target Architecture

Use a control-plane design:

```text
ragcli
  -> ApiClient
  -> context_engine FastAPI
  -> admin-only deployment routes
  -> LightRAGDeploymentService
  -> deployment backend implementation
       - local Docker Compose implementation for dev/self-hosted
       - possible future remote/cloud implementation
  -> LightRAG domain manifest / deployment records / job records

frontend
  -> same FastAPI routes
```

The FastAPI backend becomes the single API surface for both CLI and frontend.

---

## Key Architectural Boundaries

### `context_engine` owns

- users and auth
- admin authorization
- deployment API routes
- domain/knowledge-base registry
- job records and status
- audit logs
- mapping app-facing knowledge-base/domain IDs to LightRAG deployments
- calling LightRAG via HTTP adapter
- exposing graph/retrieval/admin capabilities to frontend and CLI

### LightRAG owns

- document ingestion internals
- vector indexes
- graph indexes
- retrieval behavior
- graph data
- its own runtime process/container

### `ragcli` owns

- command parsing
- credential use
- backend API calls
- human/json rendering
- no deployment business logic
- no local Docker orchestration, except perhaps a tiny dev-only bootstrap helper if explicitly approved

---

## Non-Negotiable Constraints

1. **API-first**
   - Every new real `ragcli` command must map to a backend API route.
   - If no route exists, the command must return `not_supported_by_backend`.

2. **Frontend-ready**
   - Design every route so a future admin frontend can use it.
   - Avoid CLI-specific backend behavior.
   - Return stable JSON models.

3. **Admin-only deployment**
   - Create/delete/start/stop/recreate deployment actions must require backend admin authorization.
   - The CLI must not infer admin privileges locally.

4. **Do not copy LightRAG internals into `app/`**
   - Keep retrieval, upload, status, and graph communication HTTP-only.
   - Deployment orchestration may manage containers/scripts, but retrieval must go through the remote adapter.

5. **Keep implementation lean**
   - No Kubernetes, Celery, elaborate plugin system, or multi-cloud abstraction in v1.
   - Use a small service interface only if it prevents coupling.

6. **Test without live Docker**
   - Unit/route tests must mock deployment backend operations.
   - Do not require a running LightRAG service for normal tests.

7. **Safe output**
   - Never print API keys, passwords, tokens, full env files, or secret headers.
   - CLI JSON output must be stable.

---

## Planning Questions To Answer

Before proposing the implementation, answer these:

1. What current `ragcli` commands exist, and what routes do they mirror?
2. What LightRAG deployment capabilities exist in `easy-deploy-lightrag`?
3. Which of those capabilities should become backend admin API routes?
4. Which capabilities should be deferred?
5. What backend route names should be added?
6. What CLI commands should mirror those routes?
7. What stable JSON response shapes should the future frontend consume?
8. What database or manifest changes are needed beyond the current read-only `LIGHTRAG_DOMAIN_MANIFEST` support?
9. Should deployment state live in database tables, manifest files, or both?
10. What minimum background job/status model is needed for long-running deployment operations?
11. What should happen if Docker is unavailable?
12. How should secrets be generated, stored, masked, and rotated?
13. How does rollback work?
14. What is the smallest safe Phase 1?

---

## Proposed API Surface To Evaluate

Evaluate and refine this proposed API surface.

### Knowledge-base / LightRAG domain management

```http
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
DELETE /admin/lightrag/domains/{domain_id}
```

### Deployment lifecycle

```http
POST /admin/lightrag/domains/{domain_id}/deploy
POST /admin/lightrag/domains/{domain_id}/start
POST /admin/lightrag/domains/{domain_id}/stop
POST /admin/lightrag/domains/{domain_id}/restart
POST /admin/lightrag/domains/{domain_id}/recreate
GET  /admin/lightrag/domains/{domain_id}/status
```

### Regeneration / config

```http
POST /admin/lightrag/domains/{domain_id}/regenerate
GET  /admin/lightrag/domains/{domain_id}/config
```

Config response must mask secrets.

### Logs / events

```http
GET /admin/lightrag/domains/{domain_id}/events
GET /admin/lightrag/domains/{domain_id}/logs
```

Logs may be deferred if unsafe or too much for v1.

### Jobs

Prefer using existing job patterns if available:

```http
GET  /jobs/{job_id}
POST /jobs/{job_id}/retry
```

Long-running deployment operations should return a `job_id`.

---

## Proposed CLI Surface To Evaluate

These commands should only exist if the backend route exists.

```bash
ragcli admin lightrag domains list
ragcli admin lightrag domains create --name NAME --port PORT
ragcli admin lightrag domains show --domain-id DOMAIN_ID
ragcli admin lightrag domains delete --domain-id DOMAIN_ID

ragcli admin lightrag deployments deploy --domain-id DOMAIN_ID
ragcli admin lightrag deployments start --domain-id DOMAIN_ID
ragcli admin lightrag deployments stop --domain-id DOMAIN_ID
ragcli admin lightrag deployments restart --domain-id DOMAIN_ID
ragcli admin lightrag deployments recreate --domain-id DOMAIN_ID
ragcli admin lightrag deployments status --domain-id DOMAIN_ID

ragcli admin lightrag deployments regenerate --domain-id DOMAIN_ID
ragcli admin lightrag deployments config --domain-id DOMAIN_ID
ragcli admin lightrag deployments events --domain-id DOMAIN_ID
```

You may recommend shorter aliases if they remain clear, for example:

```bash
ragcli admin lightrag domain list
ragcli admin lightrag domain create
ragcli admin lightrag domain deploy
ragcli admin lightrag domain status
```

But explain the tradeoff.

---

## Important Design Decision

Do not expose raw local shell commands as the primary model.

Avoid this as the main design:

```bash
ragcli lightrag domain up
```

unless it maps to:

```http
POST /admin/lightrag/domains/{domain_id}/start
```

The backend must be the source of truth so the frontend can perform the same operation.

---

## Backend Service Design To Consider

Propose a minimal backend module structure, such as:

```text
app/api/routes/admin_lightrag.py
app/services/lightrag_deployment_service.py
app/services/deployment_backends/
  __init__.py
  base.py
  local_compose.py
app/integrations/lightrag_domains.py
app/integrations/lightrag_remote_adapter.py
app/storage/repositories/lightrag_domains.py
```

Keep this lean. Do not create unnecessary abstractions.

A useful interface might be:

```python
class DeploymentBackend:
    def create_domain(...)
    def deploy(...)
    def start(...)
    def stop(...)
    def restart(...)
    def delete(...)
    def status(...)
    def regenerate(...)
```

But only introduce it if it helps separate route code from Docker/process logic.

---

## Storage Design To Consider

Design a simple v1 state model.

At minimum, a domain/knowledge-base record needs:

```text
id
name
slug
base_url
port
status
created_by_user_id
created_at
updated_at
deployment_backend
external_engine
manifest_path or runtime_ref
metadata_json
```

If using manifest files from `easy-deploy-lightrag`, decide whether the database is the source of truth or the manifest is the source of truth.

Recommendation to evaluate:

- Database is the app source of truth.
- Manifest/files are generated runtime artifacts.
- Add a reconciliation/status route to compare DB vs actual runtime.

---

## Frontend Readiness Requirements

Every backend route should return frontend-friendly JSON.

Do not return unstructured shell output as the primary response.

Prefer shapes like:

```json
{
  "domain": {
    "id": "kb_123",
    "name": "AbleMed Manuals",
    "slug": "ablemed-manuals",
    "base_url": "http://localhost:9621",
    "status": "running",
    "health": "healthy",
    "created_at": "2026-05-14T10:00:00Z",
    "updated_at": "2026-05-14T10:05:00Z"
  }
}
```

For long-running operations:

```json
{
  "job_id": "job_123",
  "operation": "deploy",
  "domain_id": "kb_123",
  "status": "queued"
}
```

For status:

```json
{
  "domain_id": "kb_123",
  "deployment_status": "running",
  "health": "healthy",
  "base_url": "http://localhost:9621",
  "last_checked_at": "2026-05-14T10:10:00Z",
  "details": {
    "container_status": "running"
  }
}
```

For config:

```json
{
  "domain_id": "kb_123",
  "config": {
    "base_url": "http://localhost:9621",
    "port": 9621,
    "api_key": "***",
    "env_path": "external/lightrag/data/domains/ablemed/.env"
  }
}
```

---

## Required Implementation Plan Sections

Return a markdown plan with:

1. Executive summary
2. Why the previous local-only CLI plan is insufficient for frontend use
3. Current codebase map
4. `easy-deploy-lightrag` capability inventory
5. Proposed backend API routes
6. Proposed mirrored `ragcli` commands
7. Frontend/admin UX implications
8. Backend service/module design
9. Storage/source-of-truth design
10. Deployment backend strategy
11. Security/secrets strategy
12. Error/output contracts
13. TDD implementation phases
14. Source-to-target migration table
15. Risks and mitigations
16. Explicit deferrals
17. Phase 1 coding-agent task

---

## TDD Expectations

Create vertical slices:

### Phase 1: API contract and route skeleton

- Add tests for admin-only LightRAG domain list/create/show.
- Non-admin gets `403`.
- CLI commands call those routes through fake API client.
- No Docker yet.

### Phase 2: Domain registry

- Persist domain records.
- Validate slug/name/port.
- Return stable JSON for frontend and CLI.
- Add masked config response.

### Phase 3: Deployment service with mocked local backend

- Add deploy/start/stop/status route tests.
- Mock Docker/process calls.
- Return `job_id` or stable operation responses.

### Phase 4: Adapt easy-deploy-lightrag behavior

- Port only the minimal required manifest/env/compose generation.
- Keep helpers small and deterministic.
- Never print secrets.

### Phase 5: CLI mirrored commands

- Add `ragcli admin lightrag ...`.
- Ensure every command maps to a backend route.
- Human and JSON outputs are tested.

### Phase 6: Frontend readiness checks

- Confirm all route responses are stable and UI-friendly.
- Add route examples to docs.
- Add OpenAPI/schema notes if project uses them.

---

## Explicit Deferrals Unless Already Present

Defer these unless the codebase already has simple support:

- multi-host deployment
- Kubernetes
- cloud provider deployment
- live streaming logs
- secret rotation UI
- graph editing
- complex retrieval profiles
- per-user knowledge-base deployment permissions beyond admin-only
- Celery/Redis queue if existing job system is sufficient
- frontend implementation itself

---

## Acceptance Criteria For The Plan

The final plan must make it obvious that:

- `ragcli` mirrors backend routes.
- The future admin frontend can use the same routes.
- Deployment operations are backend admin actions.
- The CLI does not directly manage Docker as the primary implementation.
- LightRAG retrieval remains behind the HTTP adapter.
- The code remains junior-developer-readable.
- Tests do not require live LightRAG or Docker.
