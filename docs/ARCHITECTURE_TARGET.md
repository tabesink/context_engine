# Target Architecture

This is the lean target architecture for the active Context Engine app. It records the intended ownership boundaries after the final architecture cleanup, using current product vocabulary instead of historical job/provider/domain overlap.

## Ownership Rule

```text
Documents = uploaded files plus parsed local structure
Domains = LightRAG runtime/workspace identity
Operations = async work visible through product APIs
Providers = admin-managed model profiles and secrets with env fallback
Frontend = typed API helpers and focused stores
```

## Boundaries

- Documents own uploaded file records, local storage paths, parsed pages, sections, blocks, source chunks, assets, and current document availability.
- Domains own the LightRAG runtime/workspace identity selected for upload, retrieval, graph browsing, and managed deployment.
- Operations own async visibility for document ingest, retry, status refresh, and domain lifecycle work. The database table may remain `jobs`, but product APIs and frontend language should use operations.
- Provider configuration is intentionally hybrid: DB-backed profiles and encrypted secrets are admin-managed runtime configuration, while environment variables bootstrap defaults and fallback secrets.
- The frontend should call backend routes through `client/src/lib/api` modules or focused stores. Components should not hardcode product backend URLs directly.

## Canonical Surfaces

- Document processing progress is read through `processing-status`.
- Async/global activity is read through `/operations`.
- Domain lifecycle is create, start, stop, and delete.
- Provider diagnostics and settings live under `/admin/ai-settings`.
- Retrieval returns evidence, not a composed assistant answer.

## Compatibility Rules

- `ingestion-status` may remain as a deprecated compatibility wrapper until all clients are migrated.
- `/jobs` should not be mounted as a normal product API. Keep the internal table/repository naming until a deliberate storage migration is planned.
- Destructive schema changes require the guardrails in `docs/DATABASE_OWNERSHIP.md`.
