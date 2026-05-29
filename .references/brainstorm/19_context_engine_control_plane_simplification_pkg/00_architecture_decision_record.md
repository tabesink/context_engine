# ADR: Lean Control-Plane Storage Model

## Status

Proposed for phased implementation.

## Context

The current runtime schema stores users, documents, jobs, audit logs, query logs, local document structure/assets, LightRAG domain lifecycle state, and AI provider settings.

The schema is mostly reasonable, but the current complexity comes from these patterns:

1. The domain is represented as a lifecycle table, not a first-class product object.
2. Jobs are document-centric even though domain operations also exist.
3. State appears in multiple places without an explicit ownership contract.
4. Document structure uses both scalar pointers and JSON reverse arrays for the same relationships.
5. Some settings names are narrow and may become awkward as the app grows.

## Decision

Adopt this control-plane model:

```text
users
  Own auth identity and authorization role.

documents
  Own stable document registry and current document availability.

lightrag_domains
  Own domain identity, domain lifecycle, runtime health, and immutable embedding/runtime constraints.

operations
  Own all async task progress for document, domain, provider, and system work.

audit_logs
  Own immutable who-did-what history.

query_logs
  Own retrieval telemetry.

document_pages / sections / blocks / source_chunks / assets
  Own local document navigation/read-model data.

ai_model_profiles / ai_provider_secrets / runtime_settings
  Own AI provider control-plane configuration.
```

## Key architecture rule

```text
operations.status is the source of truth for active/recent work.
documents.status is a cached/current document availability rollup.
lightrag_domains.state is a cached/current domain availability rollup.
audit_logs are append-only history.
query_logs are retrieval telemetry.
```

## Consequences

Positive:

- Domain lifecycle code becomes easier to reason about.
- Frontend polling can read one operation model for all long-running tasks.
- Domain actions and document ingestion share one progress contract.
- Document structure integrity becomes less fragile because duplicate reverse arrays are removed.
- UI can expose fewer admin lifecycle verbs without losing backend traceability.

Tradeoffs:

- Requires migrations and compatibility handling.
- Requires repository/service refactor, not just table renaming.
- Requires tests around status rollups and document navigation output.

## Decision boundaries

This ADR does not mandate collapsing document structure into a single `document_nodes` table. That is an optional future simplification only if the current pages/sections/blocks/chunks/assets split becomes a real burden.
