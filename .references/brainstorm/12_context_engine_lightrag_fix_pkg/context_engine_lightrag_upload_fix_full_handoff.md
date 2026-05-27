# Context Engine — LightRAG Upload Fix Implementation Package

This package is a handoff for a junior developer and coding agent to cleanly fix the document upload failure:

> `LightRAG service unavailable`

Working diagnosis:

> The API/worker containers cannot resolve or connect to the managed LightRAG domain service name, e.g. `lightrag_fatigue`, even though the host machine can reach `127.0.0.1:9622`.

This is a Docker runtime boundary issue: host-to-container reachability is not the same as API-container-to-LightRAG-container reachability.

## Goal

Make LightRAG domain resolution, domain lifecycle, document upload validation, graph access, and ingestion use one lean backend contract:

```text
One domain registry -> one runtime URL resolver -> one health probe -> all upload/retrieval/graph/worker paths
```

Do not scatter host URL vs container URL decisions across services.

## Package contents

| File | Purpose |
|---|---|
| `docs/01_problem_diagnosis.md` | Explains the failure mode and why host `127.0.0.1` tests can be misleading. |
| `docs/02_target_architecture.md` | Defines the lean architecture after cleanup. |
| `docs/03_implementation_plan.md` | Step-by-step implementation plan divided into PR-sized phases. |
| `docs/04_file_change_map.md` | Concrete files to inspect/change and expected responsibilities. |
| `docs/05_acceptance_criteria.md` | Definition of done and pass/fail checks. |
| `runbooks/docker_dns_debug_runbook.md` | Commands to verify `lightrag_fatigue` DNS/reachability from API and worker containers. |
| `runbooks/domain_repair_runbook.md` | Manual and future automated domain repair flow. |
| `patch_skeletons/runtime_url_resolver.py` | Skeleton for dynamic host/container URL resolution. |
| `patch_skeletons/domain_health_probe.py` | Skeleton for centralized LightRAG health probing. |
| `patch_skeletons/admin_repair_endpoint.py` | Skeleton for `POST /admin/lightrag/domains/{domain_id}/repair`. |
| `tests/test_plan.md` | Unit/integration/manual test matrix. |
| `prompts/coding_agent_prompt.md` | Ready-to-paste coding-agent prompt. |
| `checklists/junior_dev_checklist.md` | Practical checklist for implementation and review. |

## Recommended implementation order

1. Confirm DNS/reachability from inside `api` and `worker`.
2. Add dynamic runtime URL resolution.
3. Fix generated Compose networking and aliases.
4. Add central health probe.
5. Add admin repair operation.
6. Wire upload/graph/retrieval/worker paths through the same resolver/probe.
7. Add tests and manual smoke checks.

## Non-goals

- Do not embed LightRAG directly into Context Engine.
- Do not make LightRAG a library dependency inside the API process.
- Do not introduce multiple new domain models.
- Do not create duplicate upload/retrieval flows.
- Do not make the frontend parse Docker details.

# 01 — Problem Diagnosis

## Symptom

Document upload fails with:

```text
LightRAG service unavailable
```

Likely internal cause:

```text
API container cannot resolve or connect to lightrag_fatigue
```

Example mistaken assumption:

```text
Host can hit http://127.0.0.1:9622, therefore the API can reach LightRAG.
```

That assumption is false in Docker.

Inside the `api` container, `127.0.0.1` means the API container itself, not the LightRAG container. The API should reach a managed LightRAG domain through Docker DNS, for example:

```text
http://lightrag_fatigue:9621
```

not:

```text
http://127.0.0.1:9622
```

## Code observations from current repo

The current repository structure indicates:

1. `docker-compose.yml` places `api`, `worker`, `status-poller`, `postgres`, and `redis` on a shared `context_engine_lightrag` network.
2. `app/lightrag_deploy/service.py` creates per-domain LightRAG service names like `lightrag_<domain_id>` and computes:
   - `host_base_url`
   - `container_base_url`
   - `base_url`
3. `app/services/lightrag_domain_registry.py` currently reads `base_url` directly from the persisted manifest.
4. `app/integrations/lightrag_remote_adapter.py` expects a registered domain `base_url` and maps connect/timeouts into `LightRAGServiceUnavailable`.
5. `app/services/document_service.py` validates the LightRAG domain before upload/ingestion.

## Most likely root cause

The domain manifest or generated Compose state has drifted from the active Docker runtime:

```text
Manifest says domain is running/configured
        ↓
API resolves runtime URL from stale persisted base_url
        ↓
API tries lightrag_fatigue or 127.0.0.1 incorrectly
        ↓
Docker DNS/connect fails
        ↓
LightRAGServiceUnavailable / HTTP 503
```

## Why this should be fixed structurally

The code currently stores `base_url` as if it were stable configuration. But `base_url` is actually a runtime decision:

```text
If API is inside Docker network -> use container_base_url
If caller is host/local shell -> use host_base_url
```

Persisting this decision causes stale-manifest bugs when runtime mode changes or when a domain is regenerated.

## Design principle

Persist stable deployment facts. Compute runtime connection URLs.

Stable manifest fields:

```json
{
  "id": "fatigue",
  "service_name": "lightrag_fatigue",
  "host_port": 9622,
  "container_port": 9621,
  "host_base_url": "http://127.0.0.1:9622",
  "container_base_url": "http://lightrag_fatigue:9621"
}
```

Computed runtime field:

```text
runtime_base_url = container_base_url in Docker socket mode
runtime_base_url = host_base_url outside Docker/socket mode
```
# 02 — Target Architecture

## Target flow

```text
Admin creates LightRAG domain
        ↓
Domain manifest stores stable deployment facts
        ↓
Generated Compose attaches lightrag_<domain> to context_engine_lightrag network
        ↓
API/worker resolve runtime URL dynamically
        ↓
Health probe checks DNS + HTTP reachability from runtime context
        ↓
Upload only proceeds if domain is reachable
        ↓
Worker ingests using same resolver and same domain contract
        ↓
Graph/retrieval use same resolver and health diagnostics
```

## Core simplification

Only one backend component should decide between:

```text
host_base_url      e.g. http://127.0.0.1:9622
container_base_url e.g. http://lightrag_fatigue:9621
```

That component should be the domain registry/resolver.

## Proposed components

### 1. `LightRAGDomainRegistry`

Responsibilities:

- Read domain manifest.
- Filter unavailable/blocked domains.
- Resolve a requested domain.
- Return a runtime domain object with a computed `base_url`.
- Hide host/container URL selection from callers.

Anti-responsibilities:

- Should not start containers.
- Should not know detailed Docker command behavior.
- Should not perform upload or retrieval.

### 2. `LightRAGRuntimeUrlResolver`

Can be a private method inside `LightRAGDomainRegistry` at first. Extract only if it grows.

Responsibilities:

- Given a domain manifest entry and settings, return the runtime URL.
- Prefer `container_base_url` in Docker/socket mode.
- Prefer `host_base_url` in host/local mode.
- Fall back carefully for legacy manifests.

### 3. `LightRAGDomainHealthProbe`

Responsibilities:

- Check whether the runtime URL is reachable.
- Return structured reason codes:
  - `ok`
  - `dns_failed`
  - `connect_error`
  - `connection_refused`
  - `timeout`
  - `http_error`
  - `bad_response`
- Never mutate domain state directly unless explicitly asked by a lifecycle service.

### 4. `LightRAGDomainService`

Responsibilities:

- Create domains.
- Regenerate generated Compose/env files.
- Start/stop/recreate containers.
- Archive/permanently delete domain data.
- Update manifest lifecycle status.

Important change:

- `up()` should not mark a domain healthy only because Docker Compose returned exit code `0`.
- It may mark it `starting` or `running_unverified` first, then health probe confirms `running` + `is_healthy=true`.

### 5. Admin repair endpoint

New endpoint:

```text
POST /admin/lightrag/domains/{domain_id}/repair
```

Responsibilities:

1. Regenerate domain env/Compose.
2. Ensure Docker network exists.
3. Start/recreate the domain service.
4. Probe runtime reachability.
5. Persist accurate status.
6. Return diagnostics.

## Target API-level behavior

### Upload failure before fix

```text
LightRAG service unavailable
```

### Upload failure after cleanup

User-facing:

```text
LightRAG domain 'fatigue' is not reachable from the API runtime. Ask an admin to repair the domain.
```

Logs/internal diagnostics:

```json
{
  "domain_id": "fatigue",
  "runtime_base_url": "http://lightrag_fatigue:9621",
  "service_name": "lightrag_fatigue",
  "reason": "dns_failed",
  "hint": "Verify generated LightRAG container is attached to context_engine_lightrag network."
}
```

## Leanness rule

Do not create parallel domain abstractions unless necessary. Prefer improving the existing registry + lifecycle service:

```text
Good:
app/services/lightrag_domain_registry.py
app/lightrag_deploy/service.py
app/services/lightrag_domain_health.py

Avoid:
app/services/lightrag_domain_registry_v2.py
app/services/lightrag_runtime_registry.py
app/services/domain_manager_copy.py
```
# 03 — Implementation Plan

## Phase 0 — Reproduce and confirm

### Steps

1. Start the app normally.
2. Ensure the `fatigue` domain exists in the manifest/admin UI.
3. From host, confirm host URL works:

```bash
a curl -fsS http://127.0.0.1:9622/ || true
```

4. From inside API container, test Docker DNS:

```bash
docker compose exec api getent hosts lightrag_fatigue
```

5. From inside worker container, test Docker DNS:

```bash
docker compose exec worker getent hosts lightrag_fatigue
```

6. From inside API container, test HTTP:

```bash
docker compose exec api python - <<'PY'
import httpx
for path in ["/", "/health", "/healthz"]:
    url = f"http://lightrag_fatigue:9621{path}"
    try:
        r = httpx.get(url, timeout=5)
        print(url, r.status_code, r.text[:200])
    except Exception as exc:
        print(url, type(exc).__name__, exc)
PY
```

### Expected finding

Host URL may work while container DNS fails.

That confirms the issue is domain wiring, not necessarily LightRAG availability.

---

## Phase 1 — Runtime URL resolver cleanup

### Objective

Stop trusting persisted `base_url` as the canonical runtime connection URL.

### Files

```text
app/services/lightrag_domain_registry.py
app/lightrag_deploy/service.py
app/lightrag_deploy/models.py
tests/services/test_lightrag_domain_registry.py
```

### Changes

1. Add a helper:

```python
def _runtime_base_url(entry: dict[str, Any]) -> str:
    ...
```

2. In Docker/socket mode, use `container_base_url`.
3. In host/local mode, use `host_base_url`.
4. Use legacy `base_url` only as fallback.
5. Return `LightRAGDomainRuntime.base_url` as the computed value.
6. Optionally add `runtime_base_url` to the dataclass for clarity, but avoid breaking callers if `base_url` is already widely used.

### Acceptance

Unit tests prove:

```text
socket mode -> http://lightrag_fatigue:9621
host mode   -> http://127.0.0.1:9622
legacy only -> uses base_url with warning/log
missing all -> raises LightRAGDomainRegistryInvalidError
```

---

## Phase 2 — Generated Compose network contract

### Objective

Ensure every managed LightRAG service is discoverable from `api`, `worker`, and `status-poller`.

### Files

```text
app/lightrag_deploy/compose.py
app/lightrag_deploy/settings.py
tests/lightrag_deploy/test_compose_generator.py
```

### Required generated Compose behavior

For domain `fatigue`, generated service should include:

```yaml
services:
  lightrag_fatigue:
    networks:
      context_engine_lightrag:
        aliases:
          - lightrag_fatigue

networks:
  context_engine_lightrag:
    external: true
```

### Acceptance

After domain up/repair:

```bash
docker compose exec api getent hosts lightrag_fatigue
docker compose exec worker getent hosts lightrag_fatigue
```

Both must return an IP.

---

## Phase 3 — Health probe

### Objective

Centralize reachability checks and structured error reasons.

### New file

```text
app/services/lightrag_domain_health.py
```

### Behavior

The probe should:

1. Resolve the runtime domain using `LightRAGDomainRegistry`.
2. Try DNS resolution for the runtime hostname.
3. Try HTTP GET to one or more safe endpoints.
4. Return a structured result.

### Suggested result model

```python
@dataclass(frozen=True)
class LightRAGDomainHealth:
    domain_id: str
    base_url: str
    ok: bool
    reason: str | None = None
    detail: str | None = None
    status_code: int | None = None
```

### Acceptance

DNS failure returns:

```json
{
  "ok": false,
  "reason": "dns_failed"
}
```

HTTP connection failure returns:

```json
{
  "ok": false,
  "reason": "connect_error"
}
```

HTTP 200/204/404 on safe endpoint can be treated carefully. Prefer a known LightRAG health endpoint if available; otherwise a successful TCP/HTTP response from `/` can be considered reachable.

---

## Phase 4 — Admin repair operation

### Objective

Give admin a single action to fix stale/wrong managed-domain wiring.

### Files

```text
app/api/admin/lightrag_admin.py
app/lightrag_deploy/service.py
app/services/lightrag_domain_health.py
tests/api/test_lightrag_admin_repair.py
```

### Endpoint

```text
POST /admin/lightrag/domains/{domain_id}/repair
```

### Internal flow

```text
load domain
regenerate env + compose
ensure docker network exists if possible
recreate/start domain service
probe runtime URL
persist accurate status
return diagnostics
```

### Response shape

```json
{
  "domain_id": "fatigue",
  "service_name": "lightrag_fatigue",
  "host_base_url": "http://127.0.0.1:9622",
  "container_base_url": "http://lightrag_fatigue:9621",
  "runtime_base_url": "http://lightrag_fatigue:9621",
  "docker_operation": "succeeded",
  "health": {
    "ok": true,
    "reason": null,
    "status_code": 200
  },
  "status": "running"
}
```

---

## Phase 5 — Upload guardrail

### Objective

Prevent uploads from being accepted when the target LightRAG runtime is unreachable.

### Files

```text
app/services/document_service.py
app/services/lightrag_ingestion_service.py
app/workers/worker.py
```

### Changes

Before enqueueing upload/ingestion:

1. Validate domain exists.
2. Validate lifecycle status is available.
3. Run health probe or use recent cached health if implemented.
4. If unreachable, fail early with actionable detail.

### Error message

```text
LightRAG domain 'fatigue' is not reachable from the API runtime. Run domain repair and retry upload.
```

### Acceptance

If DNS fails:

- upload does not enqueue a job
- API returns a controlled error
- logs include `domain_id`, `runtime_base_url`, and `reason`

---

## Phase 6 — Graph/retrieval consistency

### Objective

Ensure graph and retrieval paths use the same runtime domain resolution as upload.

### Files to inspect

```text
app/api/**/graph*.py
app/api/**/query*.py
app/api/**/retrieve*.py
app/services/**graph*.py
app/services/**retrieval*.py
app/integrations/lightrag_remote_adapter.py
```

### Rule

No caller should construct LightRAG URLs manually.

All LightRAG access should look like:

```python
domain = registry.validate_available(domain_id)
adapter = LightRAGRemoteAdapter(base_url=domain.base_url, api_key=domain.api_key)
```

or:

```python
adapter = LightRAGRemoteAdapter.for_domain(domain_id)
```

with `for_domain()` internally using the same registry.

---

## Phase 7 — Frontend/admin UX cleanup

### Objective

Make the issue obvious and repairable in the admin UI.

### UI behavior

In LightRAG domain settings:

```text
Domain: fatigue
Status: Unreachable from API runtime
Runtime URL: http://lightrag_fatigue:9621
Host URL: http://127.0.0.1:9622
Action: Repair domain
```

Do not show Docker details to regular users.

Regular upload users should only see:

```text
This knowledge graph is temporarily unavailable. Ask an admin to repair the domain.
```

Admin users should see:

```text
DNS failed for lightrag_fatigue from API container. Repair domain or check Docker network context_engine_lightrag.
```
# 04 — File Change Map

## High-priority files

### `app/services/lightrag_domain_registry.py`

Current role:

- Reads domain manifest.
- Lists domains.
- Validates a requested domain is active/available.
- Returns `LightRAGDomainRuntime` with a `base_url`.

Required change:

- Compute `base_url` at runtime from `host_base_url` / `container_base_url` based on settings.
- Treat persisted `base_url` as legacy fallback only.

Review notes:

- Keep this as the central resolver.
- Do not create a second registry unless unavoidable.

---

### `app/lightrag_deploy/service.py`

Current role:

- Creates LightRAG domain manifest entries.
- Generates domain env files.
- Writes generated Compose.
- Starts/stops/recreates domain services.
- Persists domain status.

Required change:

- `create_domain()` should still store `host_base_url` and `container_base_url`.
- Avoid treating stored `base_url` as canonical.
- `up()` / `recreate()` should not mark `is_healthy=true` without a runtime health check.
- Add/coordinate repair operation.

---

### `app/lightrag_deploy/compose.py`

Current role:

- Generates Compose file for managed LightRAG domains.

Required change:

- Ensure generated domain services attach to the same network as API/worker.
- Add explicit alias equal to `service_name`.
- Use external network name from settings, defaulting to `context_engine_lightrag`.

Expected generated YAML pattern:

```yaml
services:
  lightrag_fatigue:
    networks:
      context_engine_lightrag:
        aliases:
          - lightrag_fatigue

networks:
  context_engine_lightrag:
    external: true
```

---

### `app/lightrag_deploy/settings.py`

Current role:

- Holds deploy settings for LightRAG domain generation.

Required change:

- Ensure there is a single network setting.
- Ensure default container port is separate from host port start.
- Ensure execution mode is normalized, e.g. `socket` vs `host`.

Recommended settings:

```text
LIGHTRAG_DOCKER_NETWORK=context_engine_lightrag
LIGHTRAG_DOCKER_EXECUTION_MODE=socket
LIGHTRAG_DEFAULT_CONTAINER_PORT=9621
LIGHTRAG_DEFAULT_PORT_START=9622
```

---

### `app/integrations/lightrag_remote_adapter.py`

Current role:

- Makes HTTP calls to LightRAG.
- Converts LightRAG responses into Context Engine evidence/upload responses.
- Maps HTTP connection failures to `LightRAGServiceUnavailable`.

Required change:

- Keep this adapter thin.
- Do not add Docker-specific logic here.
- Ensure `for_domain()` uses the single registry/resolver.
- Log `domain_id` and `base_url` around connection errors if practical.

---

### `app/services/document_service.py`

Current role:

- Handles document upload validation and domain checks.

Required change:

- Before accepting/enqueueing upload, check domain availability and runtime reachability.
- Return actionable upload failure when target domain is unreachable.

---

### `app/api/admin/lightrag_admin.py`

Current role:

- Admin routes for LightRAG lifecycle operations.

Required change:

- Add repair route:

```text
POST /admin/lightrag/domains/{domain_id}/repair
```

- Return diagnostic payload with runtime URL and health result.

---

## New recommended file

### `app/services/lightrag_domain_health.py`

Purpose:

- Central structured health probe for managed LightRAG domains.

Responsibilities:

- Resolve domain runtime URL.
- Check DNS if hostname is not localhost/IP.
- Check HTTP reachability.
- Return reason codes.

Do not:

- Start/stop containers.
- Mutate manifests unless explicitly orchestrated by lifecycle/admin service.

---

## Tests to add/update

```text
tests/services/test_lightrag_domain_registry.py
tests/services/test_lightrag_domain_health.py
tests/lightrag_deploy/test_compose_generator.py
tests/api/test_lightrag_admin_repair.py
tests/services/test_document_service_lightrag_guardrail.py
```
# 05 — Acceptance Criteria

## Functional acceptance

### A. DNS verification

For a managed domain `fatigue`, these commands must work:

```bash
docker compose exec api getent hosts lightrag_fatigue
docker compose exec worker getent hosts lightrag_fatigue
```

Expected:

```text
An IP address is returned for lightrag_fatigue.
```

---

### B. Runtime URL resolution

Given manifest values:

```json
{
  "id": "fatigue",
  "host_base_url": "http://127.0.0.1:9622",
  "container_base_url": "http://lightrag_fatigue:9621"
}
```

When `LIGHTRAG_DOCKER_EXECUTION_MODE=socket`, resolved runtime URL must be:

```text
http://lightrag_fatigue:9621
```

When execution mode is host/local, resolved runtime URL must be:

```text
http://127.0.0.1:9622
```

---

### C. Health probe

If the service name cannot resolve:

```json
{
  "ok": false,
  "reason": "dns_failed"
}
```

If DNS resolves but HTTP fails:

```json
{
  "ok": false,
  "reason": "connect_error"
}
```

If LightRAG responds successfully:

```json
{
  "ok": true
}
```

---

### D. Admin repair endpoint

Calling:

```text
POST /admin/lightrag/domains/fatigue/repair
```

must:

1. Regenerate domain env/Compose.
2. Start/recreate domain service.
3. Probe runtime URL.
4. Persist correct status.
5. Return diagnostic JSON.

Expected success response includes:

```json
{
  "domain_id": "fatigue",
  "runtime_base_url": "http://lightrag_fatigue:9621",
  "health": {
    "ok": true
  },
  "status": "running"
}
```

---

### E. Upload behavior

If LightRAG runtime is reachable:

```text
Upload succeeds or enqueues ingestion normally.
```

If LightRAG runtime is not reachable:

```text
Upload fails before enqueueing ingestion.
```

Response should be actionable:

```text
LightRAG domain 'fatigue' is not reachable from the API runtime. Run domain repair and retry upload.
```

---

### F. No duplicate domain logic

Search the codebase for URL construction:

```bash
grep -R "127.0.0.1:962" -n app tests || true
grep -R "lightrag_" -n app | grep "http" || true
grep -R "container_base_url\|host_base_url\|base_url" -n app
```

Expected:

- URL selection logic exists only in the registry/resolver.
- Adapter receives a ready `base_url`.
- Upload/retrieval/graph callers do not choose host vs container URL themselves.

---

## Regression acceptance

Existing behaviors must remain:

- Admin-only domain lifecycle operations.
- Domain list visible for selection where intended.
- Existing upload API contract unless currently broken.
- Existing retrieval/graph API contracts.
- Domain archival/permanent delete semantics.
- Embedding lock behavior per domain.

## Review checklist

A reviewer should reject the PR if:

- A new duplicate domain registry is introduced without removing the old one.
- Upload path manually builds LightRAG URLs.
- Adapter learns Docker/network details.
- Repair endpoint returns success without checking reachability.
- Domain status is set to healthy only because Docker Compose returned exit code `0`.
# Docker DNS Debug Runbook

Use this when uploads fail with:

```text
LightRAG service unavailable
```

## 1. Confirm host-level access

From host machine:

```bash
curl -v http://127.0.0.1:9622/
```

If this works, it only proves host-to-LightRAG published port access.

It does not prove API-to-LightRAG access.

## 2. Confirm API container DNS

```bash
docker compose exec api getent hosts lightrag_fatigue
```

Expected:

```text
172.x.x.x lightrag_fatigue
```

If it fails:

```text
DNS/network wiring is broken.
```

## 3. Confirm worker container DNS

```bash
docker compose exec worker getent hosts lightrag_fatigue
```

The worker must also resolve the domain because ingestion jobs may run there.

## 4. Test HTTP from API container

```bash
docker compose exec api python - <<'PY'
import httpx
urls = [
    "http://lightrag_fatigue:9621/",
    "http://lightrag_fatigue:9621/health",
    "http://lightrag_fatigue:9621/healthz",
]
for url in urls:
    try:
        r = httpx.get(url, timeout=5)
        print(url, r.status_code, r.text[:300])
    except Exception as exc:
        print(url, type(exc).__name__, exc)
PY
```

## 5. Test HTTP from worker container

```bash
docker compose exec worker python - <<'PY'
import httpx
try:
    r = httpx.get("http://lightrag_fatigue:9621/", timeout=5)
    print(r.status_code, r.text[:300])
except Exception as exc:
    print(type(exc).__name__, exc)
PY
```

## 6. Inspect Docker network

```bash
docker network inspect context_engine_lightrag
```

Look for:

```text
api
worker
status-poller
lightrag_fatigue
```

If `lightrag_fatigue` is absent, generated Compose did not attach it to the correct network.

## 7. Inspect generated LightRAG Compose

Find generated Compose path from app settings or logs, then confirm:

```yaml
networks:
  context_engine_lightrag:
    external: true
```

and service:

```yaml
services:
  lightrag_fatigue:
    networks:
      context_engine_lightrag:
        aliases:
          - lightrag_fatigue
```

## 8. Common fixes

### If host URL works but container DNS fails

Regenerate and repair domain.

### If DNS works but HTTP fails

Container may be starting, unhealthy, or LightRAG server not listening on container port `9621`.

Check logs:

```bash
docker logs lightrag_fatigue --tail 200
```

### If API resolves wrong hostname

Check domain manifest and runtime resolver.

Expected runtime URL in Docker/socket mode:

```text
http://lightrag_fatigue:9621
```
# Domain Repair Runbook

## Purpose

Repair a managed LightRAG domain whose manifest/Compose/runtime wiring has drifted.

Example broken domain:

```text
fatigue
```

Expected service name:

```text
lightrag_fatigue
```

## Manual repair flow today

Use existing admin lifecycle endpoints or CLI/TUI if available.

Recommended sequence:

```text
1. Stop domain if running.
2. Regenerate domain env and generated Compose.
3. Start/recreate domain.
4. Verify API container can resolve lightrag_fatigue.
5. Verify worker container can resolve lightrag_fatigue.
6. Verify API can make HTTP request to http://lightrag_fatigue:9621.
7. Retry upload.
8. Verify graph/retrieval endpoints.
```

## Future one-click repair endpoint

Add:

```text
POST /admin/lightrag/domains/{domain_id}/repair
```

Expected behavior:

```text
load domain
normalize service/container names
regenerate env
regenerate Compose
ensure Docker network exists
start/recreate service
health probe runtime URL
persist status
return diagnostics
```

## Suggested repair response

```json
{
  "domain_id": "fatigue",
  "service_name": "lightrag_fatigue",
  "host_base_url": "http://127.0.0.1:9622",
  "container_base_url": "http://lightrag_fatigue:9621",
  "runtime_base_url": "http://lightrag_fatigue:9621",
  "docker_operation": "succeeded",
  "health": {
    "ok": true,
    "reason": null,
    "status_code": 200
  },
  "status": "running"
}
```

## Repair failure examples

### DNS failed

```json
{
  "health": {
    "ok": false,
    "reason": "dns_failed",
    "detail": "Name or service not known"
  },
  "hint": "Verify lightrag_fatigue is attached to context_engine_lightrag."
}
```

### Connection refused

```json
{
  "health": {
    "ok": false,
    "reason": "connect_error",
    "detail": "Connection refused"
  },
  "hint": "Check LightRAG container logs and ensure it listens on 9621."
}
```

### Timeout

```json
{
  "health": {
    "ok": false,
    "reason": "timeout"
  },
  "hint": "LightRAG may still be starting or blocked on provider/model configuration."
}
```
# Test Plan

## Unit tests

### `test_lightrag_domain_registry.py`

Cases:

1. Socket mode returns `container_base_url`.
2. Host mode returns `host_base_url`.
3. Legacy manifest with only `base_url` still works.
4. Missing URL fields raises `LightRAGDomainRegistryInvalidError`.
5. Unavailable statuses still block domain usage.
6. Blocked/archived lifecycle domains do not appear in regular list.

Example assertions:

```python
def test_socket_mode_uses_container_url(tmp_path):
    registry = make_registry(tmp_path, docker_execution_mode="socket")
    domain = registry.get_required("fatigue")
    assert domain.base_url == "http://lightrag_fatigue:9621"
```

---

### `test_compose_generator.py`

Cases:

1. Generated LightRAG service attaches to `context_engine_lightrag`.
2. Generated service has alias equal to `service_name`.
3. Network is declared as external.
4. Host port is published only as needed.
5. Container port remains stable at `9621`.

Expected YAML pattern:

```yaml
services:
  lightrag_fatigue:
    networks:
      context_engine_lightrag:
        aliases:
          - lightrag_fatigue
```

---

### `test_lightrag_domain_health.py`

Cases:

1. DNS failure -> `reason="dns_failed"`.
2. HTTP connect error -> `reason="connect_error"`.
3. HTTP timeout -> `reason="timeout"`.
4. HTTP 200 root -> `ok=True`.
5. HTTP 404 root but reachable -> decide policy; if accepted as reachable, document it.
6. HTTP 500 on all probe endpoints -> `reason="bad_response"`.

Use monkeypatch/respx/httpx mock as appropriate.

---

### `test_lightrag_admin_repair.py`

Cases:

1. Repair calls regenerate.
2. Repair calls recreate/up.
3. Repair runs health probe.
4. Repair returns diagnostic response.
5. Failed health marks response as unhealthy rather than silently succeeded.

---

### `test_document_service_lightrag_guardrail.py`

Cases:

1. Upload with healthy domain proceeds.
2. Upload with DNS-failed domain fails before job enqueue.
3. Error includes domain id but does not leak secrets.
4. Worker ingestion uses same runtime resolver as API upload path.

## Integration tests

### Docker integration smoke test

1. Start stack.
2. Create/repair domain `fatigue`.
3. Confirm DNS:

```bash
docker compose exec api getent hosts lightrag_fatigue
docker compose exec worker getent hosts lightrag_fatigue
```

4. Upload a small text/PDF document.
5. Confirm ingestion job completes.
6. Query/retrieve evidence.
7. Open graph endpoint/UI and confirm graph response returns.

## Manual QA

### Admin UI

- Domain list shows reachable/unreachable status.
- Admin can click repair.
- Admin sees runtime URL diagnostics.
- Non-admin users do not see Docker internals.

### Upload UX

- Healthy domain: upload succeeds.
- Broken domain: user sees actionable error.
- After repair: retry upload succeeds.

## Regression checks

Run:

```bash
pytest
```

Run targeted tests:

```bash
pytest tests/services/test_lightrag_domain_registry.py
pytest tests/services/test_lightrag_domain_health.py
pytest tests/lightrag_deploy/test_compose_generator.py
pytest tests/api/test_lightrag_admin_repair.py
```

Run grep checks:

```bash
grep -R "127.0.0.1:962" -n app tests || true
grep -R "container_base_url\|host_base_url\|base_url" -n app | sort
```

Reviewer must confirm that host/container URL choice exists in one place only.
# Coding Agent Prompt — Fix Context Engine LightRAG Upload DNS / Domain Wiring

You are a senior backend engineer working in the `context_engine` repository.

## User problem

Document upload fails with:

```text
LightRAG service unavailable
```

The suspected root cause is that the API/worker containers cannot resolve or connect to a managed LightRAG domain service such as:

```text
lightrag_fatigue
```

The host machine may successfully reach:

```text
http://127.0.0.1:9622
```

but that does not prove the API/worker containers can reach LightRAG. Inside Docker, API and worker should use:

```text
http://lightrag_fatigue:9621
```

## Objective

Cleanly fix this issue with low entropy and minimal duplication.

Implement one central runtime domain resolver, one health probe, and one admin repair flow. Do not scatter Docker networking decisions across upload, graph, retrieval, and worker code.

## Constraints

- Keep LightRAG as an HTTP service boundary.
- Do not embed/import LightRAG directly into the Context Engine process.
- Do not create duplicate domain registry models unless you remove/merge the older one.
- Do not let upload/retrieval/graph code manually choose host URL vs container URL.
- Preserve admin-only write/domain lifecycle operations.
- Preserve regular user domain selection/retrieval behavior.
- Preserve existing API contracts unless a small additive change is required.

## Review first

Inspect these files:

```text
app/services/lightrag_domain_registry.py
app/lightrag_deploy/service.py
app/lightrag_deploy/compose.py
app/lightrag_deploy/settings.py
app/lightrag_deploy/models.py
app/integrations/lightrag_remote_adapter.py
app/services/document_service.py
app/services/lightrag_ingestion_service.py
app/api/admin/lightrag_admin.py
docker-compose.yml
```

Also search:

```bash
grep -R "LightRAGRemoteAdapter" -n app tests
grep -R "resolve_lightrag_domain\|lightrag_domain" -n app tests
grep -R "host_base_url\|container_base_url\|base_url" -n app tests
grep -R "9621\|9622\|lightrag_" -n app tests docker-compose.yml
```

## Implementation requirements

### 1. Runtime URL resolution

Modify the registry/resolver so runtime URL is computed dynamically:

```text
socket/Docker mode -> container_base_url
host/local mode    -> host_base_url
legacy fallback    -> base_url
```

`LightRAGDomainRuntime.base_url` should represent the computed runtime URL.

### 2. Generated Compose networking

Ensure generated LightRAG domain services attach to the same Docker network as API/worker/status-poller:

```yaml
networks:
  context_engine_lightrag:
    external: true
```

For each service:

```yaml
services:
  lightrag_fatigue:
    networks:
      context_engine_lightrag:
        aliases:
          - lightrag_fatigue
```

### 3. Health probe

Add a centralized health probe in:

```text
app/services/lightrag_domain_health.py
```

It should return structured results:

```text
ok
dns_failed
connect_error
timeout
http_error
bad_response
```

### 4. Admin repair endpoint

Add:

```text
POST /admin/lightrag/domains/{domain_id}/repair
```

Flow:

```text
load domain
regenerate env/compose
recreate or start service
health probe runtime URL
persist accurate status
return diagnostics
```

Do not mark a domain healthy just because Docker Compose returned `0`.

### 5. Upload guardrail

Before accepting/enqueueing document upload, validate that the domain is reachable from the API runtime. If not reachable, return an actionable error:

```text
LightRAG domain 'fatigue' is not reachable from the API runtime. Run domain repair and retry upload.
```

### 6. Worker consistency

Ensure worker ingestion uses the same runtime resolver as API upload/retrieval.

## Tests to add/update

```text
tests/services/test_lightrag_domain_registry.py
tests/services/test_lightrag_domain_health.py
tests/lightrag_deploy/test_compose_generator.py
tests/api/test_lightrag_admin_repair.py
tests/services/test_document_service_lightrag_guardrail.py
```

## Manual smoke test

After implementation:

```bash
docker compose up -d --build
```

Repair domain:

```text
POST /admin/lightrag/domains/fatigue/repair
```

Verify:

```bash
docker compose exec api getent hosts lightrag_fatigue
docker compose exec worker getent hosts lightrag_fatigue
```

Then upload a small document and verify retrieval/graph.

## Definition of done

- API and worker can resolve `lightrag_fatigue`.
- Runtime URL in Docker mode is `http://lightrag_fatigue:9621`.
- Host URL can still be used where appropriate outside Docker.
- Upload fails early with clear error if domain unreachable.
- Admin repair endpoint fixes stale domain wiring.
- No duplicate LightRAG domain selection logic exists.
- Tests pass.
# Junior Developer Checklist

## Before coding

- [ ] Pull latest `main`.
- [ ] Start stack locally.
- [ ] Create or identify `fatigue` LightRAG domain.
- [ ] Confirm current upload failure.
- [ ] Run DNS checks from `api` and `worker` containers.
- [ ] Capture current domain manifest entry for `fatigue`.

## During coding

### Runtime resolver

- [ ] Find where `LightRAGDomainRuntime.base_url` is set.
- [ ] Change it to compute runtime URL.
- [ ] Do not remove legacy `base_url` support until migration is planned.
- [ ] Add unit tests for socket/host/legacy modes.

### Compose

- [ ] Find generated LightRAG Compose code.
- [ ] Add/confirm external network.
- [ ] Add/confirm service alias.
- [ ] Add test for generated YAML.

### Health probe

- [ ] Add `app/services/lightrag_domain_health.py`.
- [ ] Return structured health result.
- [ ] Test DNS failure.
- [ ] Test HTTP failure.
- [ ] Test success.

### Repair endpoint

- [ ] Add admin endpoint.
- [ ] Regenerate domain before start/recreate.
- [ ] Run health probe after Docker operation.
- [ ] Persist accurate status.
- [ ] Return diagnostics.

### Upload guardrail

- [ ] Add pre-upload reachability check.
- [ ] Do not enqueue ingestion job if domain unreachable.
- [ ] Make error actionable.
- [ ] Ensure no API keys/secrets leak in error response.

## Before PR

- [ ] Run `pytest`.
- [ ] Run targeted LightRAG tests.
- [ ] Run grep check for duplicate URL logic.
- [ ] Manually repair `fatigue`.
- [ ] Confirm API can resolve `lightrag_fatigue`.
- [ ] Confirm worker can resolve `lightrag_fatigue`.
- [ ] Upload test document.
- [ ] Query/retrieve evidence.
- [ ] Test graph endpoint/UI.

## Reviewer questions to answer in PR description

1. Where is the single source of truth for runtime LightRAG URL selection?
2. How does the system detect DNS failure differently from HTTP timeout?
3. What happens if Docker Compose returns success but LightRAG is not reachable?
4. How does an admin repair a broken domain?
5. How does the upload path avoid enqueueing doomed ingestion jobs?
