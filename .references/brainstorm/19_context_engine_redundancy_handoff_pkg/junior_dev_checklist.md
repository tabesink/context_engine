# Junior Developer Checklist — Lean Redundancy Tasks

Use this checklist for safe low-risk tasks before the bigger service refactor.

## Task 1 — Document Lifecycle Semantics

- [ ] Add comments/docstrings explaining `repair`, `recreate`, and `regenerate`.
- [ ] Confirm no route behavior changed.
- [ ] Run backend tests.

## Task 2 — Admin UI Action Cleanup

- [ ] Find LightRAG domain action buttons/menu.
- [ ] Keep normal actions: Start, Stop, Repair, Archive, Preview Purge, Purge.
- [ ] Hide Recreate and Regenerate from normal UI.
- [ ] Ensure Purge requires preview/confirmation.
- [ ] Run frontend lint/build.

## Task 3 — Shared Failure Normalizer

- [ ] Create `app/services/lightrag_failure_normalizer.py`.
- [ ] Move duplicated missing-secret regex/normalization logic there.
- [ ] Update `DocumentService` and `LightRAGIngestionService` to use it.
- [ ] Add tests for missing provider secret messages.
- [ ] Run targeted tests.

## Task 4 — Frontend API Helper Cleanup

- [ ] Replace custom fetch/token/error handling in `client/src/api/lightrag.ts` with `apiRequest()`.
- [ ] Keep domain path helper.
- [ ] Confirm graph routes still call Context Engine, not LightRAG.
- [ ] Run frontend lint/build.

## Task 5 — Type Alignment

- [ ] Add a frontend type matching `/lightrag/domains` response.
- [ ] Do not reuse old `LightRagDomain` shape unless adapter maps it.
- [ ] Add or update VisualAsset mapping.
- [ ] Run TypeScript build.
