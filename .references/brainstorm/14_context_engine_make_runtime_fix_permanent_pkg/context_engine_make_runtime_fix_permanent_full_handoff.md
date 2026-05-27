# Context Engine — Make LightRAG Runtime Fix Permanent

Date: 2026-05-27

## Goal

Convert the current local runtime workaround into a permanent, low-entropy implementation:

- LightRAG managed domains using PostgreSQL must provision their database role/database/extensions before startup.
- Legacy containers that still use `POSTGRES_USER=lightrag` must be intentionally supported through a compatibility mode, not manual SQL drift.
- Generated `domain.env` files must be deterministic and must never point LightRAG at a non-existent Postgres role.
- Managed LightRAG containers must have reliable tokenizer/tiktoken startup in Docker, without external DNS dependency during container boot.
- Admin repair must regenerate env, provision Postgres, recreate the domain, and return actionable diagnostics.

## Why this is needed

The temporary fix created compatibility database objects manually:

- role: `lightrag`
- database: `lightrag`
- privileges
- `vector` extension

That made the legacy `lightrag_fatigue` container healthy, but it is not permanent because a clean `docker compose down -v`, fresh developer machine, CI run, or new managed domain can recreate the same failure.

## Package contents

- `docs/00_current_review.md` — current codebase review based on the modified repo.
- `docs/01_target_architecture.md` — permanent storage and container-start architecture.
- `docs/02_implementation_plan.md` — PR-sized phases for a junior dev/coding agent.
- `docs/03_repair_runbook.md` — commands to verify and repair current stack.
- `docs/04_acceptance_tests.md` — concrete test matrix.
- `docs/05_coding_agent_prompt.md` — ready-to-paste prompt.
- `patches/` — implementation skeletons.
- `scripts/diagnose_lightrag_runtime.sh` — local diagnostic script.
- `sql/bootstrap_lightrag_compat.sql` — legacy compatibility bootstrap SQL.
- `tests/` — test skeletons.

## Important target decision

Use **Postgres-backed LightRAG** permanently, but with explicit provisioning:

```text
Context Engine app DB/user:
  context_engine / context_engine

Managed domain DB/user:
  lightrag_<domain> / lightrag_<domain>

Legacy compatibility DB/user:
  lightrag / lightrag
```

Do not rely on manual SQL fixes.


# 00 — Current Review

## Current symptom

The temporary runtime fix worked because it created the missing compatibility objects:

```text
role: lightrag
database: lightrag
extension: vector
```

That explains why the error stopped:

```text
FATAL: password authentication failed for user "lightrag"
DETAIL: Role "lightrag" does not exist.
```

and why `http://127.0.0.1:9622/health` became healthy.

## What the current codebase still does

### 1. Domain creation always assigns per-domain Postgres names

`LightRAGDomainService.create_domain()` currently sets:

```python
postgres_database=f"{self.settings.postgres_database_prefix}_{postgres_suffix}"
postgres_user=f"{self.settings.postgres_user_prefix}_{postgres_suffix}"
```

This means a domain like `fatigue` is intended to have:

```text
postgres_database = lightrag_fatigue
postgres_user     = lightrag_fatigue
```

That is good, but incomplete unless those DB objects are actually provisioned before container startup.

### 2. `domain.env` still renders runtime/app DB credentials instead of per-domain credentials

`render_domain_env()` currently renders the Postgres storage block when `domain.postgres_database` and `domain.postgres_user` exist, but uses:

```python
POSTGRES_DATABASE={settings.runtime_postgres_database}
POSTGRES_USER={settings.runtime_postgres_user}
POSTGRES_PASSWORD={settings.runtime_postgres_password}
```

This is the central bug. It mixes app runtime database credentials with LightRAG domain-level database identity.

The permanent fix is:

```python
POSTGRES_DATABASE={domain.postgres_database}
POSTGRES_USER={domain.postgres_user}
POSTGRES_PASSWORD={settings.lightrag_postgres_password}
```

or, if using compatibility mode:

```python
POSTGRES_DATABASE=lightrag
POSTGRES_USER=lightrag
POSTGRES_PASSWORD={settings.lightrag_postgres_password}
```

### 3. There is no Postgres provisioner

The code creates the manifest/env/compose, but it does not create:

- Postgres role
- Postgres database
- required extensions
- privileges

So the current system can generate a `domain.env` that references a role/database that does not exist.

### 4. `up()` and `recreate()` do not repair dependencies

`LightRAGDomainService.up()` currently writes compose and starts the domain. It should first provision Postgres objects and regenerate `domain.env`.

Target order:

```text
get domain
ensure paths
ensure Postgres role/database/extensions
write domain.env
write compose
recreate/up container
probe health
persist status
```

### 5. Registry still trusts persisted `base_url`

`LightRAGDomainRegistry.get_required()` reads `base_url` directly from manifest. This is fragile because Docker mode can change. Runtime URL should be computed:

```text
socket mode -> container_base_url
host mode   -> host_base_url
```

### 6. Tokenizer DNS startup issue remains separate

The managed `context_engine_lightrag_fatigue` container is failing due tokenizer/tiktoken DNS startup. The Dockerfile currently downloads tiktoken cache during build, but runtime still needs an explicit offline/stable cache path. Permanent fix:

- Mount/cache tiktoken files inside the image.
- Set `TIKTOKEN_CACHE_DIR` in generated `domain.env`.
- Avoid startup-time downloads.
- Optionally set tokenizer cache fallback env vars used by LightRAG/tiktoken.

## Conclusion

The current temporary SQL fix is valid as a compatibility bridge, but the permanent implementation must happen in the domain lifecycle service.


# 01 — Target Architecture

## Permanent goal

LightRAG domain lifecycle owns all runtime prerequisites.

When admin starts or repairs a domain:

```text
Admin API
  -> LightRAGDomainService.repair(domain_id)
  -> PostgresProvisioner.ensure_for_domain(domain)
  -> write_domain_env(domain)
  -> ComposeGenerator.write(domains)
  -> Docker Compose recreate/up
  -> HealthProbe.check(domain runtime URL)
  -> update manifest status
```

## Storage modes

### Mode 1 — `per_domain` recommended

Each managed LightRAG domain gets isolated Postgres objects:

```text
domain_id: fatigue
database:  lightrag_fatigue
role:      lightrag_fatigue
workspace: fatigue
```

Pros:

- no app DB table mixing
- easy to drop/purge one domain later
- clearer debugging
- safer for multi-user/admin-only write app

### Mode 2 — `compat`

Used only to permanently support existing legacy containers that are hard-coded to:

```env
POSTGRES_DATABASE=lightrag
POSTGRES_USER=lightrag
```

This mode should be explicit, visible in diagnostics, and ideally temporary.

### Mode 3 — `app_database_shared` not recommended

LightRAG uses `context_engine` database/user. Avoid this unless you deliberately want app metadata and LightRAG storage tables mixed.

## New settings

Add to `app/core/config.py` and `app/lightrag_deploy/settings.py`:

```env
LIGHTRAG_STORAGE_BACKEND=postgres
LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain
LIGHTRAG_POSTGRES_COMPAT_ENABLED=true
LIGHTRAG_POSTGRES_COMPAT_DATABASE=lightrag
LIGHTRAG_POSTGRES_COMPAT_USER=lightrag
LIGHTRAG_POSTGRES_COMPAT_PASSWORD=lightrag
LIGHTRAG_POSTGRES_ADMIN_DATABASE=context_engine
LIGHTRAG_POSTGRES_VECTOR_EXTENSION=vector
LIGHTRAG_POSTGRES_AGE_EXTENSION=age
LIGHTRAG_TOKENIZER_OFFLINE=true
LIGHTRAG_TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

Allowed provisioning modes:

```text
per_domain
compat
app_database_shared
```

Default recommendation:

```env
LIGHTRAG_STORAGE_BACKEND=postgres
LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain
LIGHTRAG_POSTGRES_COMPAT_ENABLED=true
```

This means new managed domains use `lightrag_<domain>`, but the system also creates `lightrag/lightrag` compatibility objects for old containers until you delete them.

## New service

Create:

```text
app/lightrag_deploy/postgres_provisioner.py
```

Responsibilities:

- connect to admin/runtime DB as `context_engine`
- create role if missing
- create database if missing
- grant privileges
- create `vector` extension in target DB
- create `age` extension where available
- return diagnostics, do not hide failed extension setup

## New repair endpoint

Add:

```http
POST /admin/lightrag/domains/{domain_id}/repair
```

It should:

1. provision Postgres objects
2. optionally provision legacy compatibility DB/role
3. regenerate `domain.env`
4. regenerate generated compose
5. recreate container
6. health-probe runtime URL
7. return exact diagnostics


# 02 — Implementation Plan

## PR 1 — Add settings

Files:

```text
app/core/config.py
app/lightrag_deploy/settings.py
.env.example
.env.lightrag-deploy.example
```

Add settings:

```python
lightrag_storage_backend: str = "postgres"
lightrag_postgres_provisioning_mode: str = "per_domain"
lightrag_postgres_compat_enabled: bool = True
lightrag_postgres_compat_database: str = "lightrag"
lightrag_postgres_compat_user: str = "lightrag"
lightrag_postgres_compat_password: str = "lightrag"
lightrag_postgres_admin_database: str = "context_engine"
lightrag_postgres_vector_extension: str = "vector"
lightrag_postgres_age_extension: str = "age"
lightrag_tokenizer_offline: bool = True
lightrag_tiktoken_cache_dir: str = "/app/.cache/tiktoken"
```

Validation:

- `LIGHTRAG_STORAGE_BACKEND` in `{postgres,file}`
- `LIGHTRAG_POSTGRES_PROVISIONING_MODE` in `{per_domain,compat,app_database_shared}`
- if storage backend is postgres, require postgres host/port/user/password values.

## PR 2 — Fix `render_domain_env()`

File:

```text
app/lightrag_deploy/compose.py
```

Current bug:

```python
POSTGRES_DATABASE={settings.runtime_postgres_database}
POSTGRES_USER={settings.runtime_postgres_user}
POSTGRES_PASSWORD={settings.runtime_postgres_password}
```

Replace with one helper:

```python
def _lightrag_postgres_credentials(domain, settings):
    if settings.postgres_provisioning_mode == "compat":
        return compat db/user/password
    if settings.postgres_provisioning_mode == "app_database_shared":
        return runtime db/user/password
    return domain.postgres_database, domain.postgres_user, settings.postgres_password
```

Then render exactly those values.

Also render tokenizer cache:

```env
TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

## PR 3 — Add `PostgresProvisioner`

Create:

```text
app/lightrag_deploy/postgres_provisioner.py
```

Use `psycopg` if already installed; otherwise use SQLAlchemy/engine from app storage. The provisioner needs autocommit for `CREATE DATABASE`.

API:

```python
@dataclass(frozen=True)
class ProvisioningResult:
    database: str
    user: str
    role_exists: bool
    database_exists: bool
    vector_extension_enabled: bool
    age_extension_enabled: bool
    warnings: list[str]

class LightRAGPostgresProvisioner:
    def ensure_for_domain(self, domain: LightRAGDomain) -> ProvisioningResult: ...
    def ensure_legacy_compat(self) -> ProvisioningResult | None: ...
```

Rules:

- Never drop roles/databases in repair.
- Idempotent: safe to run on every `create`, `regenerate`, `up`, `recreate`, `repair`.
- Create extension in target DB, not only in `context_engine`.
- Catch missing `age` separately and warn, but do not hide `vector` failure when vector storage is enabled.

## PR 4 — Wire provisioner into lifecycle

File:

```text
app/lightrag_deploy/service.py
```

Add:

```python
self.postgres = postgres_provisioner or LightRAGPostgresProvisioner(self.settings)
```

Call before writing env/starting containers:

```python
create_domain()
regenerate()
up()
recreate()
repair()
```

Recommended new method:

```python
def repair(self, domain_id: str) -> LightRAGDomainRepairResult:
    domain = self.get_domain(domain_id)
    pg = self._ensure_postgres_for_domain(domain)
    write_domain_env(...)
    self.compose.write(...)
    command = self.runner.recreate(domain.service_name)
    health = self.health_probe.check(domain)
    persist status based on command + health
    return diagnostics
```

## PR 5 — Add admin repair endpoint

File:

```text
app/api/routes/lightrag_admin.py
```

Add:

```python
@router.post("/admin/lightrag/domains/{domain_id}/repair")
def repair_domain(...):
    result = service.repair(domain_id)
    audit(...)
    return result
```

Do not return 200 with hidden failure. If Docker recreate fails, return 502 and include command stderr/stdout in detail.

## PR 6 — Runtime URL resolver cleanup

File:

```text
app/services/lightrag_domain_registry.py
```

Replace persisted `base_url` trust with runtime computation:

```python
def _runtime_base_url(entry, settings):
    if settings.lightrag_docker_execution_mode == "socket":
        return entry["container_base_url"]
    return entry["host_base_url"]
```

This makes switching between host mode and Docker socket mode safe.

## PR 7 — Tokenizer DNS startup fix

Files:

```text
docker/lightrag.Dockerfile
app/lightrag_deploy/compose.py
```

Keep build-time cache download, but also ensure generated `domain.env` has:

```env
TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

Consider adding:

```Dockerfile
ENV TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
RUN mkdir -p "$TIKTOKEN_CACHE_DIR"
```

If the LightRAG startup still attempts network calls, vendor/cache the required tokenizer files into the image or switch startup to a local cache-only mode.

## PR 8 — Diagnostics script and docs

Add:

```text
scripts/diagnose-lightrag-domain.sh
docs/lightrag-postgres-managed-domains.md
```

The script should check:

- generated `domain.env`
- Postgres roles/databases
- `vector` extension in target DB
- `age` extension availability
- Docker network DNS from api/worker
- domain `/health`
- old rogue containers using legacy `POSTGRES_USER=lightrag`


# 03 — Repair Runbook

## 1. Diagnose current state

```bash
DOMAIN=fatigue
./scripts/diagnose_lightrag_runtime.sh "$DOMAIN"
```

## 2. Inspect generated env

```bash
DOMAIN=fatigue
cat .data/lightrag/domains/$DOMAIN/domain.env | grep -E 'POSTGRES|LIGHTRAG_.*STORAGE|WORKSPACE|TIKTOKEN'
```

Expected for per-domain mode:

```env
WORKSPACE=fatigue
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage
LIGHTRAG_GRAPH_STORAGE=PGGraphStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
POSTGRES_PASSWORD=<configured lightrag password>
POSTGRES_VECTOR_INDEX_TYPE=HNSW
TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

Expected for compatibility mode:

```env
POSTGRES_DATABASE=lightrag
POSTGRES_USER=lightrag
POSTGRES_PASSWORD=lightrag
```

## 3. Verify DB role and database

```bash
docker compose exec postgres psql -U context_engine -d context_engine -c "\du"
docker compose exec postgres psql -U context_engine -d context_engine -c "SELECT datname FROM pg_database WHERE datname LIKE 'lightrag%';"
```

## 4. Verify vector extension in target DB

```bash
docker compose exec postgres psql -U context_engine -d lightrag_fatigue -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec postgres psql -U context_engine -d lightrag_fatigue -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
```

## 5. Repair through API

After implementation:

```bash
curl -X POST http://127.0.0.1:8010/admin/lightrag/domains/fatigue/repair \
  -H "Authorization: Bearer $TOKEN"
```

## 6. Re-test from inside API container

```bash
docker compose exec api python - <<'PY'
import httpx, socket

host = "context_engine_lightrag_fatigue"
print(socket.gethostbyname_ex(host))
print(httpx.get("http://context_engine_lightrag_fatigue:9621/health", timeout=10).text)
PY
```

If the service name is `lightrag_fatigue`, test that too:

```bash
docker compose exec api python - <<'PY'
import httpx, socket

host = "lightrag_fatigue"
print(socket.gethostbyname_ex(host))
print(httpx.get("http://lightrag_fatigue:9621/health", timeout=10).text)
PY
```

## 7. Remove legacy container once managed container is healthy

Once `context_engine_lightrag_fatigue` is healthy and all traffic points to the managed domain URL, stop/remove old unmanaged containers that still use `POSTGRES_USER=lightrag`.


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


# 05 — Coding Agent Prompt

You are working in `https://github.com/tabesink/context_engine.git`.

Goal: make the current temporary LightRAG/Postgres runtime fix permanent.

Context:
- A legacy LightRAG container `lightrag_fatigue` was failing with:
  `FATAL: password authentication failed for user "lightrag"; Role "lightrag" does not exist`.
- A manual runtime fix created role/database `lightrag`, granted privileges, enabled `vector`, and restarted the container.
- That made `http://127.0.0.1:9622/health` healthy.
- But this must become a repeatable code-level lifecycle behavior.
- A managed container `context_engine_lightrag_fatigue` is still separately failing due tokenizer DNS startup; fix that too.

Implement the permanent fix with low entropy:

1. Add explicit LightRAG Postgres settings:
   - `LIGHTRAG_STORAGE_BACKEND=postgres`
   - `LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain`
   - `LIGHTRAG_POSTGRES_COMPAT_ENABLED=true`
   - compatibility db/user/password defaults: `lightrag`
   - tokenizer cache settings.

2. Fix `app/lightrag_deploy/compose.py`:
   - Do not render app runtime DB credentials for managed LightRAG domains.
   - Render per-domain credentials in per-domain mode.
   - Render `lightrag/lightrag` only in explicit compat mode.
   - Render `TIKTOKEN_CACHE_DIR`.

3. Add `app/lightrag_deploy/postgres_provisioner.py`:
   - idempotently create role/database/extensions/privileges.
   - create `vector` extension in each target DB.
   - create/attempt `age` extension if available.
   - support `ensure_for_domain()` and `ensure_legacy_compat()`.

4. Wire provisioner into:
   - domain create
   - regenerate
   - up
   - recreate
   - new repair endpoint.

5. Add:
   `POST /admin/lightrag/domains/{domain_id}/repair`

6. Fix runtime URL resolution:
   - socket mode uses `container_base_url`.
   - host mode uses `host_base_url`.
   - do not blindly trust persisted `base_url`.

7. Fix tokenizer DNS startup:
   - ensure LightRAG image contains required tokenizer cache.
   - generated env includes `TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken`.
   - container startup should not require public DNS for tokenizer files.

8. Add tests:
   - env rendering
   - provisioner idempotency
   - repair lifecycle
   - registry runtime URL selection.

Acceptance:
- `docker compose down -v && docker compose up --build` can create/repair `fatigue` without manual SQL.
- No Postgres logs show `Role "lightrag" does not exist`.
- No `type "vector" does not exist` errors.
- Managed container health returns healthy.
- Upload -> worker ingest -> LightRAG status polling works.
