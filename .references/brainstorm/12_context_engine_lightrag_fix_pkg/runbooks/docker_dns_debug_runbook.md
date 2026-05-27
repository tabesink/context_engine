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
