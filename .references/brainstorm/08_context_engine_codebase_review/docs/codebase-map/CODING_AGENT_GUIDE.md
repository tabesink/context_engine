# Coding Agent Guide

## Purpose

This guide tells coding agents and junior developers where to make changes safely in `context_engine`.

## First Files to Read

Read in this order:

```text
README.md
AGENTS.md
app/main.py
app/core/config.py
app/core/deps.py
app/api/routes/retrieve.py
app/services/retrieval_service.py
app/retrieval/strategies.py
app/retrieval/lightrag_remote_engine.py
app/retrieval/rich_navigation_engine.py
app/integrations/lightrag_remote_adapter.py
app/api/routes/admin.py
app/api/routes/lightrag_admin.py
app/storage/tables.py
docker-compose.yml
```

## Common Change Types

### Add a new API endpoint

Work in:

```text
app/api/routes/
app/api/schemas/ or equivalent schema module
app/services/
tests/api/
```

Rules:

- keep route thin
- create or reuse a service method
- add auth/admin dependency
- add tests
- update API docs

### Change retrieval behavior

Work in:

```text
app/services/retrieval_service.py
app/retrieval/
tests/test_retrieval_*.py
```

Rules:

- do not add duplicate query endpoints
- keep `/retrieve` canonical
- do not call LightRAG directly from route handlers
- preserve stable evidence response shape

### Add provider support

Work in:

```text
app/core/config.py
app/integrations/
app/services/lightrag_domain_service.py
docs/
.env.example
```

Rules:

- do not scatter provider-specific env logic
- prefer provider profiles or adapter config
- update docs and tests

### Change LightRAG domain lifecycle

Work in:

```text
app/api/routes/lightrag_admin.py
app/services/lightrag_domain_service.py
app/services/lightrag_domain_registry.py
app/core/config.py
docker-compose.yml
tests/test_lightrag_*.py
```

Rules:

- admin-only
- preserve domain registry consistency
- do not change storage paths casually
- test create/start/stop/delete/recreate flows

### Change document ingestion

Work in:

```text
app/api/routes/admin.py
app/services/document_service.py
app/workers/
app/storage/
tests/test_document_*.py
```

Rules:

- admin-only
- preserve original upload
- preserve status transitions
- define asset behavior clearly
- do not bypass background job tracking

### Change workspace tree

Work in:

```text
app/api/routes/workspace_tree.py
app/services/workspace_tree_service.py
app/storage/repositories/
tests/test_workspace_tree*.py
```

Rules:

- keep response lightweight
- filter by domain when requested
- avoid returning full document content by default

### Change configuration

Work in:

```text
app/core/config.py
.env.example
docker-compose.yml
docs/codebase-map/CONFIGURATION_AND_DEPLOYMENT.md
tests/test_config*.py
```

Rules:

- update `.env.example`
- add validation tests
- do not introduce undocumented env vars
- keep production guardrails

## Files to Be Careful With

High-risk files:

```text
app/core/config.py
app/storage/tables.py
alembic/versions/*
app/services/retrieval_service.py
app/integrations/lightrag_remote_adapter.py
docker-compose.yml
```

Why high-risk:

- can break deployment
- can break migrations
- can break retrieval
- can break LightRAG connectivity
- can change production security posture

## Safe Refactor Zones

Usually lower-risk:

```text
docs/
tests/fixtures/
small schema/response formatting helpers
clearly isolated evidence formatting utilities
README examples
```

Still run tests after any change.

## High-Risk Refactor Zones

Avoid casual changes in:

- auth/security
- document deletion/archive behavior
- storage paths
- migrations
- LightRAG container lifecycle
- retrieval routing
- query/evidence response contract
- provider API key handling

## Development Rules

1. Do not create a second semantic retrieval system inside `context_engine`.
2. Do not add new query APIs unless `/retrieve` cannot support the use case.
3. Do not let route handlers call LightRAG directly.
4. Do not let frontend-specific display logic leak deeply into retrieval engines.
5. Do not add env vars without updating `.env.example`.
6. Do not change storage paths without migration/backup notes.
7. Do not assume per-user private corpus exists unless an ADR and schema define it.
8. Do not use `latest` image tags for production LightRAG deployments.
9. Do not remove tests around retrieval, domain lifecycle, or ingestion without replacement.
10. Prefer incremental refactors over rewrites.

## Coding Agent Acceptance Criteria Template

For each task, include:

```md
## Goal

## Files Changed

## Behavior Before

## Behavior After

## Tests Added/Updated

## Manual Verification

## Risk Notes

## Rollback Notes
```

## Required Test Mindset

For retrieval changes, test:

- authenticated user can retrieve
- unauthenticated user cannot retrieve
- admin and regular user read behavior is as intended
- document filter respects selected domain
- unavailable LightRAG domain fails clearly
- local navigation retrieval still returns stable evidence shape
- asset enrichment does not break if no assets exist

For admin changes, test:

- regular user forbidden
- admin allowed
- job/status updated
- storage side effects are expected
- failure leaves recoverable state
