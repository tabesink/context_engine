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
