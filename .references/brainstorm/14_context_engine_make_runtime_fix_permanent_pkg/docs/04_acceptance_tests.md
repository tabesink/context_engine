# 04 — Acceptance Tests

## Unit tests

### `render_domain_env()`

- per-domain mode renders `POSTGRES_USER=lightrag_fatigue`.
- per-domain mode does not render `POSTGRES_USER=context_engine`.
- compat mode renders `POSTGRES_USER=lightrag`.
- env includes `TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken`.
- `POSTGRES_VECTOR_INDEX_TYPE=HNSW` remains present.

### `PostgresProvisioner`

Use a fake runner/connection abstraction or test database.

- creates missing role.
- creates missing database.
- does not fail when role/database already exists.
- creates `vector` extension in target DB.
- warns rather than crashes if `age` extension package is unavailable, unless graph storage requires hard failure.
- returns structured diagnostics.

### `LightRAGDomainService.repair()`

With fake runner/provisioner/health probe:

- calls provisioner before `write_domain_env`.
- calls compose write before runner recreate.
- persists `running/is_healthy=True` only when command and health both succeed.
- persists `error/is_healthy=False` when health fails.
- returns diagnostic object.

### Registry URL resolution

- socket mode returns `container_base_url`.
- host mode returns `host_base_url`.
- missing URL raises registry invalid error.

## Integration tests

### Fresh volume

```bash
docker compose down -v
docker compose up --build
```

Then:

1. seed admin
2. configure provider/profile
3. create domain `fatigue`
4. call `repair`
5. upload document
6. confirm worker job succeeds
7. confirm no Postgres auth failures

Expected logs should not include:

```text
FATAL: password authentication failed for user "lightrag"
type "vector" does not exist
```

### Existing legacy container

Given an old container using:

```env
POSTGRES_USER=lightrag
POSTGRES_DATABASE=lightrag
```

Startup should pass because compatibility provisioning creates those objects intentionally.

### Managed domain

Given generated per-domain env using:

```env
POSTGRES_USER=lightrag_fatigue
POSTGRES_DATABASE=lightrag_fatigue
```

Startup should pass because the provisioner creates those objects before Docker recreate.

## Manual verification

```bash
docker compose logs postgres --tail=200 | grep -E 'FATAL|vector|lightrag'
```

No new auth failure should appear after repair.
