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
