# Final Acceptance Criteria

The refactor is complete when all of the following are true.

## State ownership

```text
[ ] documents.status is the current document availability rollup.
[ ] lightrag_domains.state is the current domain availability rollup.
[ ] operations/jobs.status is the source of truth for active/recent work.
[ ] audit_logs are append-only and not used as current state.
[ ] query_logs are retrieval telemetry only.
[ ] metadata fields do not contain hidden status/state machines.
```

## Domain lifecycle

```text
[ ] LightRAG domains are first-class rows.
[ ] Domain create/start/stop/delete use one domain service.
[ ] Domain actions create operation rows.
[ ] Normal UI exposes only Start, Stop, Delete for existing domains.
[ ] Create is exposed as a primary page/dialog action.
[ ] repair/recreate/regenerate/purge are not normal UI actions.
```

## Jobs / operations

```text
[ ] Operation rows support document/domain/system/provider resources.
[ ] Document ingestion creates document operations.
[ ] Domain lifecycle actions create domain operations.
[ ] Existing job consumers are migrated or safely aliased.
[ ] Frontend can poll one operation endpoint for active work.
```

## Document structure

```text
[ ] Section tree is built from parent_section_id.
[ ] Blocks are listed from document_blocks.section_id.
[ ] Assets are listed from document_assets.block_id/chunk_id.
[ ] Duplicate reverse arrays are no longer required by ingestion.
[ ] Public API shape is stable or intentionally versioned.
```

## Tests

```text
[ ] Unit tests pass.
[ ] Repository tests pass.
[ ] API tests pass.
[ ] Migration upgrade works from current head.
[ ] Manual smoke test passes.
```

## Low-entropy outcome

A junior developer should be able to explain the system as:

```text
Documents know what file exists and whether it is usable.
Domains know whether LightRAG runtime is available.
Operations know what work is currently happening.
Audit logs know what happened historically.
Query logs know retrieval performance.
Document structure powers source navigation.
AI profiles/secrets configure model providers.
```
