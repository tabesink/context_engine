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
