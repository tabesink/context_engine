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
