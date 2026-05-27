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
