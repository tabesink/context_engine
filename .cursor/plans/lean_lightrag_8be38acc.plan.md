---
name: Lean LightRAG
overview: "Implement the attached lean LightRAG domain lifecycle plan as a strict clean break: public lifecycle becomes Create, Start, Stop, Delete; removed routes disappear; create rejects removed fields; retrieval defaults move to backend deployment config and are omitted from new manifests."
todos:
  - id: impact-refresh
    content: Refresh/rerun GitNexus impact checks for edited symbols, warning on any HIGH/CRITICAL results before edits.
    status: completed
  - id: env-config-red-green
    content: Add tests and implementation for deployment-owned retrieval defaults in `domain.env`.
    status: completed
  - id: strict-create-red-green
    content: Add tests and implementation for strict create payload without `start` or retrieval fields.
    status: completed
  - id: manifest-cleanup
    content: Remove `retrieval_defaults` from new manifests while tolerating old manifest input.
    status: completed
  - id: start-consolidation
    content: Move runtime artifact/provisioning prep behind `up()` and remove public repair/recreate/regenerate service paths.
    status: completed
  - id: route-cleanup
    content: Remove obsolete admin lifecycle and purge routes/imports and update route tests.
    status: completed
  - id: frontend-cleanup
    content: Simplify create UI/API payload and remove obsolete lifecycle controls.
    status: completed
  - id: docs-validation
    content: Update live docs and run focused backend/frontend validation.
    status: completed
isProject: false
---

# Lean LightRAG Lifecycle Implementation

## Confirmed Decisions
- Compatibility posture: hard break now. Remove `repair`, `recreate`, `regenerate`, `purge-preview`, and `purge` routes from OpenAPI and reject stale create payload fields such as `start`, `top_k`, and token budgets.
- Manifest policy: remove `retrieval_defaults` from new manifest writes. Keep old manifests loadable, but do not use old `retrieval_defaults` when rendering `domain.env`.
- TDD posture: implement vertical slices, one behavior test at a time, then refactor while green.

## Impact And Risk
- GitNexus impact for `LightRAGDomainService` and `LightRAGDomainCreateRequest` is MEDIUM. Directly affected files include [app/lightrag_deploy/service.py](app/lightrag_deploy/service.py), [app/api/routes/lightrag_admin.py](app/api/routes/lightrag_admin.py), [tests/test_lightrag_deploy_service.py](tests/test_lightrag_deploy_service.py), and [tests/test_api.py](tests/test_api.py).
- GitNexus impact for `write_domain_env()` and `render_domain_env()` is HIGH. Direct callers/tests include [app/lightrag_deploy/service.py](app/lightrag_deploy/service.py), [tests/test_lightrag_deploy_manifest_compose.py](tests/test_lightrag_deploy_manifest_compose.py), and [tests/test_lightrag_domain_embedding_lock.py](tests/test_lightrag_domain_embedding_lock.py). The high risk is expected because env rendering is shared by create/start/runtime prep.
- GitNexus keyword index is degraded, so before code edits I will refresh analysis if needed, then rerun symbol impacts for any additional edited functions/classes.

## Implementation Approach
1. Backend env/config slice: add deployment-level retrieval default settings in [app/core/config.py](app/core/config.py) and [app/lightrag_deploy/settings.py](app/lightrag_deploy/settings.py), then update [app/lightrag_deploy/compose.py](app/lightrag_deploy/compose.py) so `domain.env` uses deploy settings, not `domain.retrieval_defaults`.
2. Manifest/create contract slice: update [app/lightrag_deploy/models.py](app/lightrag_deploy/models.py) so `LightRAGDomainCreateRequest` is strict and excludes removed fields; update `LightRAGDomain` manifest serialization/loading behavior so new manifests omit `retrieval_defaults` while old manifests can still parse.
3. Service lifecycle slice: update [app/lightrag_deploy/service.py](app/lightrag_deploy/service.py) so `create_domain()` configures only and does not depend on retrieval defaults; consolidate useful repair/regenerate preparation into private Start-time helpers used by `up()`; remove public `repair()`, `recreate()`, and `regenerate()` after route/test callers are gone.
4. Route/API slice: update [app/api/routes/lightrag_admin.py](app/api/routes/lightrag_admin.py) to remove obsolete routes/imports/services and remove create auto-start. Keep `GET/POST /admin/lightrag/domains`, `GET /admin/lightrag/domains/{domain_id}`, `POST /up`, `POST /down`, `DELETE /admin/lightrag/domains/{domain_id}`, and `GET /lightrag/domains`.
5. Frontend slice: simplify [client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx](client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx) and [client/src/lib/api/knowledge-graph-admin.ts](client/src/lib/api/knowledge-graph-admin.ts) so create sends only identity, embedding profile, and optional host port; remove repair/recreate/regenerate/purge UI and API methods; update success copy to “Domain created. Click Start when ready.”
6. Tests/docs slice: replace old custom retrieval/repair/purge expectations with behavior tests for strict create validation, create-not-starting, Start refreshing env/compose/provisioning, env defaults from deployment settings, route removal, frontend absence of removed controls, and docs that describe the four-verb lifecycle.

## Validation
- Run focused backend tests first: `tests/test_lightrag_deploy_manifest_compose.py`, `tests/test_lightrag_deploy_service.py`, relevant `tests/test_api.py` route cases, and embedding-lock tests affected by env rendering.
- Run focused frontend checks for the settings panel/API client if test scripts exist, otherwise run TypeScript/lint/build commands available in the repo.
- Run `gitnexus_detect_changes(scope="all")` before any commit request or final handoff to verify affected symbols/flows match the intended lifecycle cleanup.