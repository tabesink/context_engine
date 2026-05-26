---
name: domain purge lifecycle
overview: Add a lightweight global LightRAG domain lifecycle so admin archive/purge operations block shared-corpus reads and writes consistently, with purge hard-deleting Context Engine documents, files, artifacts, and the active LightRAG domain root after preview and typed confirmation.
todos:
  - id: migration-domain-column
    content: Add and test `documents.lightrag_domain_id` plus a small domain lifecycle table/migration.
    status: completed
  - id: lifecycle-gates
    content: Gate uploads, retrieval, document listing, and document asset/page/chunk access by global domain lifecycle state.
    status: completed
  - id: preview-slice
    content: Implement purge preview through a public service/API path using behavior-first tests.
    status: completed
  - id: guard-slice
    content: Implement admin confirmation, permanent-delete setting guards, and `purging` transition before cleanup.
    status: completed
  - id: purge-slice
    content: Implement synchronous hard-delete cleanup for files, processing rows, jobs, documents, and active LightRAG domain root.
    status: completed
  - id: isolation-validation
    content: Verify archived/purging domains are hidden from regular users, other-domain data is untouched, and run affected backend tests plus GitNexus change detection.
    status: completed
isProject: false
---

# LightRAG Domain Lifecycle And Purge Plan

## Aligned Design Gates

- This is a global administrative lifecycle, not per-user cleanup. Admins write/archive/purge the shared corpus; regular users only read/retrieve/view evidence for active domains.
- Use a lightweight DB-backed lifecycle table as Context Engine's authoritative gate: `domain_id`, `state`, timestamps, optional error/audit metadata. Keep the LightRAG manifest focused on active runtime config and compose generation.
- Lifecycle states: `active`, `archiving`, `archived`, `purging`, `purged`, `failed`.
- Archive is separate from purge. Archive is non-destructive: set `archiving`, block new uploads/retrievals/reads for the domain, archive the LightRAG runtime folder, remove it from the active manifest, then set `archived`.
- Regular users should not list or view documents/assets/pages/chunks for archived domains. Admins can still see lifecycle/audit metadata through admin surfaces.
- First purge implementation targets active manifest domains only. Previously archived domains under `lightrag_deleted_root` are out of scope for this pass.
- Purge requires admin auth, `LIGHTRAG_ALLOW_PERMANENT_DELETE=true`, and typed confirmation via `confirm_domain_id` matching the path domain id.
- Purge is synchronous for the first implementation: set `purging` first so reads/writes are blocked immediately, then perform cleanup in the same admin request. The service boundary should be clean enough for a future background job to call the same method if data volume requires it.
- Purge is a true hard delete: cancel/fail indexing jobs for the domain, remove processing rows, clear related job references or rows as needed for FK safety, delete `documents` rows, permanently remove original uploaded files, permanently remove `storage_root/documents/{document_id}`, delete the LightRAG domain root, set `purged`, and keep only audit records.
- Add `documents.lightrag_domain_id` as the reliable indexed selector, backfilled from `metadata.lightrag.domain_id` or legacy `metadata.lightrag.domain`. Keep metadata for response compatibility, but purge queries should use the real column with a temporary metadata fallback only where needed during migration.

## Impact And Risk

GitNexus impact checks before implementation:

- `DocumentRow` in [app/storage/tables.py](app/storage/tables.py): HIGH risk, 21 direct imports across routes, services, repositories, workers, and tests. The column change will be narrow and migration-backed.
- `DocumentRepository` in [app/storage/repositories/documents.py](app/storage/repositories/documents.py): MEDIUM risk, 12 direct imports. New query/delete helpers should be additive.
- `DocumentProcessingRepository` in [app/storage/repositories/document_processing.py](app/storage/repositories/document_processing.py): MEDIUM risk, 14 direct imports. Additive cleanup helper only.
- `DocumentService` in [app/services/document_service.py](app/services/document_service.py): LOW risk. Upload will set the new domain column.
- `LightRAGDomainService` in [app/lightrag_deploy/service.py](app/lightrag_deploy/service.py): LOW risk. Reuse existing domain deletion primitives carefully or add a dedicated permanent domain-root removal path.
- `remove_domain` in [app/api/routes/lightrag_admin.py](app/api/routes/lightrag_admin.py): LOW risk. New purge routes can live alongside existing archive/delete.
- `DocumentAccessPolicy` in [app/services/document_access_policy.py](app/services/document_access_policy.py): LOW risk. Add lifecycle filtering so regular users only read ready documents in active domains.
- `RetrievalService` in [app/services/retrieval_service.py](app/services/retrieval_service.py): LOW risk. Existing validation already centralizes domain availability before retrieval.
- `LightRAGDomainRegistry` in [app/services/lightrag_domain_registry.py](app/services/lightrag_domain_registry.py): MEDIUM risk, 9 direct imports. Prefer additive lifecycle-aware availability checks over manifest refactors.

## Implementation Shape

- Add an Alembic migration after `0006_operational_list_indexes` to add nullable indexed `documents.lightrag_domain_id`, backfill it from JSON metadata for SQLite/Postgres-compatible test coverage where practical, and create a small `lightrag_domain_lifecycle` table.
- Update [app/storage/tables.py](app/storage/tables.py), [app/storage/repositories/documents.py](app/storage/repositories/documents.py), and [app/services/document_service.py](app/services/document_service.py) so uploads persist the selected LightRAG domain in both the column and existing metadata.
- Add a small repository/service for lifecycle state, e.g. [app/services/lightrag_domain_lifecycle_service.py](app/services/lightrag_domain_lifecycle_service.py), with simple methods like `get_state`, `ensure_active`, `set_archiving`, `set_archived`, `set_purging`, `set_purged`, and `set_failed`.
- Update archive/remove routing in [app/api/routes/lightrag_admin.py](app/api/routes/lightrag_admin.py) so archive transitions through lifecycle state and blocks shared reads/writes before removing the domain from the active manifest. Keep [app/lightrag_deploy/service.py](app/lightrag_deploy/service.py) focused on LightRAG runtime files/manifest/compose.
- Update [app/services/document_access_policy.py](app/services/document_access_policy.py) so `list_readable_documents`, `filter_readable_documents`, and `get_readable_document_or_404` exclude non-active domains for regular document, structure, asset, chunk, and page routes.
- Update [app/services/retrieval_service.py](app/services/retrieval_service.py), [app/services/document_service.py](app/services/document_service.py), and [app/api/routes/lightrag.py](app/api/routes/lightrag.py) so archived/archiving/purging/purged domains are not selectable and cannot receive uploads or retrievals.
- Add [app/services/domain_purge_service.py](app/services/domain_purge_service.py) with two public methods: `preview_lightrag_domain_purge(domain_id)` and `purge_lightrag_domain(domain_id, actor_id, confirm_domain_id)`.
- The preview should count all documents for the domain regardless of status, count processing rows/assets/chunks/pages/sections/blocks, count original upload paths that exist, count document artifact roots that exist, estimate bytes, and list the categories that will be deleted.
- The purge should validate active domain existence and permanent-delete enablement, set lifecycle state to `purging`, record a pre-purge audit manifest, cancel/fail indexing jobs, delete files with path confinement checks, remove processing rows in dependency-safe order, handle job references, hard-delete document rows, remove the LightRAG domain from manifest/compose and delete its root, set lifecycle state to `purged`, then record a final audit event. If cleanup fails after `purging`, set `failed` with error metadata and keep reads blocked.
- Add route models to [app/lightrag_deploy/models.py](app/lightrag_deploy/models.py) or a dedicated schema module, and expose:
  - `POST /admin/lightrag/domains/{domain_id}/purge-preview`
  - `DELETE /admin/lightrag/domains/{domain_id}/purge?confirm_domain_id={domain_id}`

## TDD Plan

Use vertical red-green slices, not a bulk test dump:

1. First API/service test: upload stores `documents.lightrag_domain_id` while preserving existing metadata response shape. Implement the column and repository support enough to pass.
2. Second test: archived domains disappear from user domain selection and regular users cannot list/view archived-domain documents/assets/pages/chunks, while other active-domain documents remain visible. Implement lifecycle state and access-policy gating.
3. Third test: archive remains non-destructive: original uploads, processing rows, and artifact folders remain on disk/DB while reads/writes/retrievals are blocked.
4. Fourth test: purge preview includes all domain documents across `uploaded`, `indexing`, `ready`, `failed`, and `deleted`, not only ready documents.
5. Fifth test: purge endpoint rejects missing/incorrect `confirm_domain_id` and rejects when permanent delete is disabled. Implement route validation and service guard.
6. Sixth test: confirmed purge sets `purging` before cleanup, blocks new reads/writes, cancels/fails indexing jobs, deletes original upload files, `storage_root/documents/{document_id}` artifact folders, processing rows, document rows, and LightRAG domain root.
7. Seventh test: purge does not touch documents/files/artifacts for another LightRAG domain.

## Validation

- Run focused tests after each slice, likely `pytest tests/test_api.py -k purge` or a new focused `tests/test_domain_purge_service.py` plus any migration tests.
- Run existing affected tests around upload, document access policy, retrieval, ingestion, document processing storage, and LightRAG deploy service.
- Run full backend test suite if the focused pass is clean.
- Before any commit, run `gitnexus_detect_changes(scope="all")` to verify affected symbols and flows match this plan.