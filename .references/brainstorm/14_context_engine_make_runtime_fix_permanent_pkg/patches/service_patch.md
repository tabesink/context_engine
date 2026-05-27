# Service lifecycle patch

In `app/lightrag_deploy/service.py`:

1. Import provisioner.
2. Add constructor dependency.
3. Ensure Postgres before env write/up/recreate.

Skeleton:

```python
from app.lightrag_deploy.postgres_provisioner import LightRAGPostgresProvisioner

class LightRAGDomainService:
    def __init__(..., postgres_provisioner: LightRAGPostgresProvisioner | None = None, ...):
        ...
        self.postgres_provisioner = postgres_provisioner or LightRAGPostgresProvisioner(self.settings)

    def _prepare_domain_runtime(self, domain: LightRAGDomain) -> dict:
        diagnostics = {}
        if self.settings.storage_backend == "postgres":
            compat = self.postgres_provisioner.ensure_legacy_compat()
            pg = self.postgres_provisioner.ensure_for_domain(domain)
            diagnostics["postgres"] = pg
            diagnostics["postgres_compat"] = compat
        write_domain_env(domain, self.settings, self.paths.ensure_domain_paths(domain.id), self._provider_secrets_for_domain(domain))
        self.compose.write(self.list_domains())
        return diagnostics
```

Call `_prepare_domain_runtime(domain)` in:

```python
create_domain()
regenerate()
up()
recreate()
repair()
```

New repair method:

```python
def repair(self, domain_id: str) -> LightRAGDomainRepairResult:
    domain = self.get_domain(domain_id)
    diagnostics = self._prepare_domain_runtime(domain)
    command = self.runner.recreate(domain.service_name)
    # optionally run health probe
    updated = self._persist_domain_status(domain, command_succeeded=command.exit_code == 0, running=command.exit_code == 0)
    return LightRAGDomainRepairResult(...)
```
