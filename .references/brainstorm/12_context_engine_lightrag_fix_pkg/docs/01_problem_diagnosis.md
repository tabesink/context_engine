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
