# Database Ownership And Migration Guardrails

This document is the live Phase 7 ownership map for Context Engine storage. Alembic remains the production schema source of truth; SQLAlchemy table models and repositories should match the current Alembic head.

## Ownership Classes

| Table | Class | Owner | Notes |
|---|---|---|---|
| `users` | Core | Auth | User identity, role, and activation state. |
| `documents` | Core | Documents | Uploaded file registry, status, domain selection, and LightRAG diagnostics metadata. |
| `document_sections` | Core | Document processing | Parsed local structure for navigation and citation context. |
| `document_pages` | Core | Document processing | Page text and geometry metadata. |
| `document_blocks` | Core heavy | Document processing | Block-level structure; keep unless evidence UI no longer needs rich layout. |
| `document_source_chunks` | Core | Document processing/retrieval | Local citation and LightRAG ingest mapping. |
| `document_assets` | Core | Document processing/retrieval UI | Figure/table payload metadata, thumbnails, and evidence asset mapping. |
| `jobs` | Core internal | Operations/workers | Internal operation storage. Product APIs expose `/operations`, not `/jobs`. |
| `audit_logs` | Useful core | Admin/audit | Actor/event history for admin workflows. |
| `query_logs` | Useful sensitive | Retrieval/admin | Query observability; treat as privacy-sensitive data. |
| `lightrag_domains` | Core | Domain lifecycle | Desired/admin-visible domain metadata. Runtime health is observed outside the row. |
| `lightrag_domain_lifecycle` | Candidate for deprecation | Domain lifecycle compatibility | Keep until operations/audit fully replace unique read/write value. |
| `ai_model_profiles` | Optional if env-only provider config wins | Provider config | Current runtime uses DB-backed profiles with environment fallback. |
| `ai_model_settings` | Optional if env-only provider config wins | Provider config | Current runtime default profile selection. |
| `ai_provider_secrets` | Optional if env-only provider config wins | Provider config | Encrypted provider secrets with environment fallback. |

## Migration Guardrails

Forward migrations must be additive unless a destructive change has completed a compatibility phase.

Before adding `drop_table`, `drop_column`, or an equivalent destructive operation to an `upgrade()` function:

1. Classify the affected table or column in this document.
2. Remove production reads before writes, then writes before schema removal.
3. Document the compatibility phase and rollback or restore path.
4. Add `DESTRUCTIVE_MIGRATION_GUARDRAIL` metadata to the migration file with `tables`, `classification`, `rationale`, `preceding_compatibility_phase`, and `rollback`.
5. Keep downgrade behavior best-effort; durable rollback for dropped data requires restoring a database backup.

Downgrades may drop schema introduced by their matching upgrade, but forward destructive migrations need the guardrail metadata because they can remove persisted user data.
