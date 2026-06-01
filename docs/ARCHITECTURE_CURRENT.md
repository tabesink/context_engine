# Current Architecture Snapshot

This snapshot describes the active codebase before the lean architecture refactor.
It is the implementation baseline, not historical planning material.

## Product Vocabulary

```text
Documents  = uploaded files plus parsed local structure
Domains    = LightRAG runtime/workspace identity
Operations = async work visible to admins and users through product APIs
Jobs       = internal storage/worker implementation detail
Providers  = admin-managed model profiles and secrets with env fallback
```

## Route Ownership

- Document read APIs live under `GET /documents...`.
- Admin document mutation and admin status APIs live under `POST/GET /admin/documents...`.
- `processing-status` is the canonical status surface.
- `ingestion-status` remains only as a deprecated compatibility endpoint.
- `/operations` is the canonical async visibility surface.
- `/jobs` is not mounted as a product API. The table name remains `jobs`, but HTTP clients use `/operations`.
- First-class managed LightRAG domain APIs live under `/admin/lightrag-domains`.
- User-safe domain listing lives at `GET /lightrag/domains`.
- Provider administration lives under `/admin/ai-settings`.

## State Ownership

- `documents.status` owns whether a document is usable: `uploaded`, `indexing`, `ready`, `failed`, or `deleted`.
- The `jobs` table stores operation rows for background work and lifecycle visibility.
- `jobs.stage` and `jobs.message` own current operation progress.
- `documents.metadata.lightrag` stores remote correlation IDs, provider fingerprints, and diagnostics only.
- `lightrag_domains` stores desired/admin-visible domain metadata.
- Generated manifest, compose, and `domain.env` files are deployment artifacts.
- Docker/HTTP health is observed runtime state.
- `audit_logs` records who did what.

## Provider Ownership

Provider configuration is intentionally hybrid:

- DB-backed AI profiles and encrypted provider secrets are the admin-managed source for runtime provider configuration.
- Environment variables are bootstrap/fallback sources for secrets and deploy settings.
- Domain creation snapshots embedding configuration into the managed domain manifest.
- Generated `domain.env` files are deployment snapshots consumed by LightRAG, not the editable source of truth.

## Frontend API Boundary

Frontend components should call typed helpers under `client/src/lib/api` or focused stores.
Direct backend URL strings should not live in presentational components. File upload may use `fetch`
inside an API helper because `FormData` needs custom handling.

