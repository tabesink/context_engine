# Service Patch Guidance

## app/lightrag_deploy/service.py

Add import:

```python
from app.lightrag_deploy.postgres_provisioner import LightRAGPostgresProvisioner
```

Update constructor:

```python
def __init__(..., postgres_provisioner: LightRAGPostgresProvisioner | None = None, ...):
    ...
    self.postgres_provisioner = postgres_provisioner or LightRAGPostgresProvisioner(self.settings)
```

Add helper:

```python
def _ensure_postgres_identity(self, domain: LightRAGDomain) -> LightRAGDomain:
    if self.settings.storage_backend != "postgres":
        return domain

    if self.settings.postgres_provisioning_mode == "shared_runtime":
        return domain.model_copy(update={
            "postgres_database": self.settings.runtime_postgres_database,
            "postgres_user": self.settings.runtime_postgres_user,
            "updated_at": self.now(),
        })

    postgres_suffix = self._postgres_identifier(domain.id)
    updates = {}
    if not domain.postgres_database:
        updates["postgres_database"] = f"{self.settings.postgres_database_prefix}_{postgres_suffix}"
    if not domain.postgres_user:
        updates["postgres_user"] = f"{self.settings.postgres_user_prefix}_{postgres_suffix}"

    if not updates:
        return domain

    updated = domain.model_copy(update={**updates, "updated_at": self.now()})
    self.manifest.update_domain(updated)
    return updated
```

In `create_domain()`:

```python
domain = LightRAGDomain(...)
domain = self._ensure_postgres_identity(domain)
if self.settings.storage_backend == "postgres":
    self.postgres_provisioner.provision_domain(domain)
write_domain_env(...)
```

In `regenerate()`:

```python
for domain in domains:
    domain = self._ensure_postgres_identity(domain)
    if self.settings.storage_backend == "postgres":
        self.postgres_provisioner.provision_domain(domain)
    write_domain_env(...)
```

Add `repair()`:

```python
def repair(self, domain_id: str) -> LightRAGDomainRepairResult:
    domain = self._ensure_postgres_identity(self.get_domain(domain_id))
    provision_result = None
    if self.settings.storage_backend == "postgres":
        provision_result = self.postgres_provisioner.provision_domain(domain)
    write_domain_env(domain, self.settings, self.paths.ensure_domain_paths(domain.id), self._provider_secrets_for_domain(domain))
    self.compose.write(self.list_domains())
    command = self.runner.recreate(domain.service_name)
    self._persist_domain_status(domain, command_succeeded=command.exit_code == 0, running=command.exit_code == 0)
    return LightRAGDomainRepairResult(...)
```
