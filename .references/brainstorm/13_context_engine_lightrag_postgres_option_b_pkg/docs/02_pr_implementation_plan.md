# 02 — PR Implementation Plan

## PR 1 — Make LightRAG storage backend explicit

### Files

```text
app/core/config.py
app/lightrag_deploy/settings.py
.env.example
```

### Add settings

```python
lightrag_storage_backend: str = "postgres"
lightrag_postgres_provisioning_mode: str = "per_domain"
lightrag_postgres_vector_index_type: str = "HNSW"
```

### Validation rules

```text
- LIGHTRAG_STORAGE_BACKEND must be one of: postgres, file.
- LIGHTRAG_POSTGRES_PROVISIONING_MODE must be one of: per_domain, shared_runtime.
- If storage backend is postgres, LIGHTRAG_POSTGRES_PASSWORD must not be blank.
```

### Acceptance

```bash
python -m pytest tests/lightrag_deploy/test_settings.py
```

---

## PR 2 — Generate domain env from the domain's provisioned DB identity

### Files

```text
app/lightrag_deploy/compose.py
```

### Required change

Current env generation must stop preferring `settings.runtime_postgres_database` and `settings.runtime_postgres_user` when rendering a domain-specific LightRAG env.

Use:

```python
POSTGRES_DATABASE=domain.postgres_database
POSTGRES_USER=domain.postgres_user
POSTGRES_PASSWORD=settings.postgres_password
```

for `per_domain` mode.

### Acceptance

For `fatigue`, generated `.data/lightrag/domains/fatigue/domain.env` contains:

```env
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
```

and does not contain:

```env
POSTGRES_USER=lightrag
POSTGRES_USER=context_engine
```

unless explicitly configured for shared runtime mode.

---

## PR 3 — Add Postgres provisioner

### New file

```text
app/lightrag_deploy/postgres_provisioner.py
```

### Responsibilities

```text
ensure_role(username, password)
ensure_database(database, owner)
ensure_database_privileges(database, username)
ensure_extensions(database): vector, AGE
check_role_exists(username)
check_database_exists(database)
```

### Idempotency

All methods must be safe to run repeatedly.

### Security

Use `psycopg.sql.Identifier` for role/database identifiers. Do not format SQL identifiers with f-strings.

---

## PR 4 — Wire provisioning into domain service

### Files

```text
app/lightrag_deploy/service.py
```

### Create domain

Before writing `domain.env`, run:

```python
self.postgres_provisioner.provision_domain(domain)
```

### Regenerate domain

Before rewriting `domain.env`, run provisioning again.

### Repair domain

Add service method:

```python
def repair(self, domain_id: str) -> LightRAGDomainRepairResult:
    domain = self.get_domain(domain_id)
    domain = self._ensure_postgres_identity(domain)
    provision = self.postgres_provisioner.provision_domain(domain)
    write_domain_env(...)
    self.compose.write(self.list_domains())
    command = self.runner.recreate(domain.service_name)
    return repair diagnostics
```

---

## PR 5 — Add admin repair endpoint

### Files

```text
app/api/routes/lightrag_admin.py
app/lightrag_deploy/models.py
```

### New route

```http
POST /admin/lightrag/domains/{domain_id}/repair
```

### Response shape

```json
{
  "id": "fatigue",
  "operation": "repair",
  "status": "succeeded",
  "service_name": "lightrag_fatigue",
  "storage_backend": "postgres",
  "postgres_database": "lightrag_fatigue",
  "postgres_user": "lightrag_fatigue",
  "postgres_role_exists": true,
  "postgres_database_exists": true,
  "extensions": {
    "vector": "ok",
    "age": "ok_or_unavailable"
  },
  "message": "Domain repaired and recreated."
}
```

---

## PR 6 — Tests

### Add tests

```text
tests/lightrag_deploy/test_postgres_provisioner.py
tests/lightrag_deploy/test_postgres_domain_env.py
tests/api/test_lightrag_admin_repair.py
```

### Acceptance

```bash
python -m pytest tests/lightrag_deploy tests/api/test_lightrag_admin_repair.py
```

---

## PR 7 — Backward-compatible migration/repair

Existing domains may already have bad/missing fields.

Repair must normalize:

```text
if domain.postgres_database is missing:
  set to lightrag_<safe_domain_id>

if domain.postgres_user is missing:
  set to lightrag_<safe_domain_id>
```

Then update manifest and regenerate env.

