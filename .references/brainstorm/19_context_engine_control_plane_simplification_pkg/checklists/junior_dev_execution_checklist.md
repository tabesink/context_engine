# Junior Developer Execution Checklist

## Before coding

```text
[ ] Pull latest main.
[ ] Run tests.
[ ] Run migrations to head.
[ ] Create a feature branch for only one phase.
[ ] Read 03_state_ownership_contract.md.
```

## Phase 1 checklist

```text
[ ] Add operation-compatible columns to jobs migration.
[ ] Update ORM row.
[ ] Add Operation domain model or compatibility alias.
[ ] Add repository methods for operation create/list/update.
[ ] Update document ingestion to use resource_type=document.
[ ] Update domain lifecycle actions to use resource_type=domain.
[ ] Keep existing job routes working or aliased.
[ ] Add tests.
```

## Phase 2 checklist

```text
[ ] Rename/promote lightrag_domain_lifecycle to lightrag_domains.
[ ] Rename ORM class to LightRAGDomainRow.
[ ] Add domain display/config/health fields.
[ ] Add repository/service methods for create/start/stop/delete.
[ ] Keep domain delete safe when documents exist.
[ ] Add domain operation rows for lifecycle actions.
[ ] Add tests.
```

## Phase 3 checklist

```text
[ ] Update repository reads to derive child section IDs.
[ ] Update repository reads to derive block IDs by section.
[ ] Update repository reads to derive asset IDs by block/chunk.
[ ] Stop ingestion from writing duplicate reverse arrays.
[ ] Confirm UI response shape remains stable.
[ ] Add tests.
[ ] Only then drop duplicate columns in later migration.
```

## What not to do

```text
[ ] Do not remove tables before replacing reads.
[ ] Do not expose repair/recreate/regenerate/purge as normal UI actions.
[ ] Do not use metadata JSON as a hidden status store.
[ ] Do not combine all phases into one PR.
[ ] Do not collapse document structure into raw JSON.
```
