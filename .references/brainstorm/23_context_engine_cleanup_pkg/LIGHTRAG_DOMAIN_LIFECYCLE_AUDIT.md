# LightRAG Domain Lifecycle Audit

## Current lifecycle model inferred from code

```text
create domain
  → validate/create metadata
  → ensure model/profile snapshots
  → ensure Postgres identity/provisioning
  → generate domain env/config artifacts
  → write Compose/service definition
  → optionally start/recover runtime
  → probe health
  → persist status
  → expose domain to users
```

## Operation map

| Operation | What it should mean | What to verify in code | Cleanup recommendation |
|---|---|---|---|
| `create` | Create domain identity/config and optionally start runtime | Whether `start=true` calls `repair` or separate start logic | Keep. Make post-create start path canonical. |
| `up` | Start existing domain runtime | Does it reprovision/write artifacts too? | Keep as Start only if semantically different from Repair. |
| `down` | Stop runtime but keep metadata/data | Does it mark health/status correctly? | Keep as Stop. |
| `recreate` | Recreate Docker service/container | Overlaps with `repair` artifact + Docker recreate flow | Deprecate/advanced. Use shared helper. |
| `repair` | Safe recovery: reprovision artifacts/runtime and return detailed status | Superset behavior of recreate | Keep canonical. |
| `regenerate` | Rewrite artifacts/Compose without canonical lifecycle action | Whether it restarts or only writes files | Hide/internal/advanced. |
| `archive` | Remove from active use without purging data | Lifecycle repository state and service remove behavior | Keep, clearly separate from purge. |
| `delete` | Legacy/compatibility route | Permanent delete rejected? | Deprecate in favor of archive/purge. |
| `purge-preview` | Show destructive impact | DomainPurgeService behavior | Keep. |
| `purge` | Permanently remove data/config | Confirmation and audit behavior | Keep with strict confirmation. |

## Main overlap: `repair` vs `recreate`

### Shared behavior to verify

Both appear to:

```text
_prepare_runtime_artifacts(domain)
compose.write(...)
_check_lightrag_build_failure(...)
runner.recreate(...)
_probe_domain_health(...)
_persist_domain_health/status(...)
```

### Difference

`repair` appears to include or expose additional provisioning/health detail and is already described as the primary recovery path.

### Recommendation

Use this structure:

```python
class LightRAGDomainService:
    def repair(self, domain_id: str) -> RepairResult:
        return self._recover_domain(domain_id, mode="repair")

    def recreate(self, domain_id: str) -> OperationResult:
        # Compatibility endpoint only.
        result = self._recover_domain(domain_id, mode="recreate_compat")
        return self._to_legacy_operation_result(result)

    def _recover_domain(self, domain_id: str, mode: str) -> RepairResult:
        # One implementation for artifact refresh + Docker recreate + health persistence.
```

Do not expose `_recover_domain` as an API route.

## Proposed lifecycle facade shape

```text
LightRAGDomainService public facade
├── create_domain
├── start_domain
├── stop_domain
├── repair_domain
├── archive_domain
├── purge_preview
└── purge_domain

Internal collaborators
├── DomainProvisioningService
├── DomainArtifactService
├── DomainRuntimeService
├── DomainHealthService
└── DomainLifecycleStateService
```

## UI recommendation

Normal admin UI should show:

- Create
- Start
- Stop
- Repair
- Archive
- Purge preview
- Purge

Advanced drawer/debug UI may show:

- Recreate compatibility
- Regenerate artifacts
- Raw health probe
- Runtime logs

## Required tests before refactor

1. Create domain with `start=false`.
2. Create domain with `start=true`.
3. Start/up existing domain.
4. Stop/down existing domain.
5. Repair successful path.
6. Repair Docker failure path.
7. Repair health failure path.
8. Recreate compatibility route returns legacy schema.
9. Regenerate does not unintentionally start/stop runtime.
10. Archive updates lifecycle state and audit log.
11. Purge requires confirmation domain id.
12. Purge preview returns expected data-impact projection.
