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
