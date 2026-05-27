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
