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
