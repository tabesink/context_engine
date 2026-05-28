# Context Engine Redundancy Hunt — Code Implementation Plan

Generated: 2026-05-28  
Repository reviewed: `https://github.com/tabesink/context_engine.git`  
Primary goal: reduce duplicate lifecycle/status/API/UI concepts before adding more LightRAG document status features.

> Execution note: the local execution container could not clone GitHub due to DNS resolution failure. This plan is based on GitHub raw/web inspection of the current public `main` branch and the supplied redundancy-hunt prompt. The coding agent should re-run the listed `rg` commands locally before applying patches.

---

## 1. Executive Summary

The biggest redundancy candidates are in the **LightRAG domain lifecycle control plane** and related state/status surfaces.

The current admin API exposes many lifecycle verbs:

- `create`
- `up`
- `down`
- `recreate`
- `repair`
- `regenerate`
- `DELETE ...?permanent=false`
- `DELETE ...?permanent=true`
- `purge-preview`
- `purge`

These operations are not all identical, but the public surface is too wide for a lean admin UX. The code should keep compatibility at the backend route level while collapsing the admin UI and internal implementation around fewer clear operations.

Recommended public/admin mental model:

1. **Create domain**
2. **Start domain**
3. **Stop domain**
4. **Repair domain** — the safe “rebuild/provision/recreate/probe” operation
5. **Archive domain** — reversible-ish soft removal from active registry
6. **Preview purge** — mandatory safety step for destructive deletion
7. **Purge domain** — irreversible full deletion of LightRAG domain + Context Engine documents/artifacts/jobs

Recommended deprecations / demotions:

- `recreate`: keep backend route temporarily as compatibility alias/advanced dev operation, but hide from normal admin UI.
- `regenerate`: demote to private/internal maintenance helper or advanced dev-only API; do not expose as normal admin action.
- `DELETE /admin/lightrag/domains/{domain_id}?permanent=true`: deprecate. It overlaps with purge but appears less complete because full purge also deletes Context Engine document rows, uploaded originals, extracted assets/tables/thumbnails, processing rows, job references, and archive roots.

No destructive route should be removed immediately. First add tests, docs/deprecation markers, and UI hiding.

---

## 2. Redundancy Inventory

| Candidate | Category | Evidence / Files | Why It Looks Redundant | Why It Might Not Be | Recommendation | Risk | Patch Size |
|---|---|---|---|---|---|---|---|
| `repair` vs `recreate` | Public API + service overlap | `app/api/routes/lightrag_admin.py`, `app/lightrag_deploy/service.py` | Both prepare Postgres identity, provision Postgres, write env, rewrite compose, build, recreate/start container, probe/persist health. | `repair` returns richer repair/provision/health response; `recreate` returns simpler operation result. | Make `Repair` the admin-facing action. Keep `recreate` as compatibility route or advanced dev route. Internally extract shared runtime-prep/build/recreate/probe helpers. | Medium: clients/tests may call recreate. | M |
| `regenerate` public route | Public API surface | `POST /admin/lightrag/domains/{id}/regenerate`, `LightRAGDomainService.regenerate()` | Regenerates Postgres/env/compose artifacts; this is closer to an internal maintenance primitive than a normal admin operation. | May be useful in dev after env/profile/provider changes. | Hide from UI; mark advanced/internal. Later move behind `repair` or CLI-only maintenance action. | Low/Medium | S |
| `create_domain(start=true)` calls `repair` | Lifecycle semantics | `create_domain()` route calls `service.create_domain()` then `service.repair()` if `start` | A create operation unexpectedly uses “repair” as start/provision/recreate bootstrap. | It ensures a fresh domain is fully provisioned and reachable. | Rename request field in UI/docs to “start after create”; optionally add service method `start_after_create()` that delegates to repair to make semantics explicit. | Low | S |
| `DELETE ...?permanent=true` vs `/purge-preview` + `/purge` | Destructive API overlap | `lightrag_admin.py`, `DomainPurgeService` | Both are permanent deletion concepts. | They are not equivalent: `DomainPurgeService` deletes CE docs, uploads, extracted artifacts, processing rows, jobs refs, archived roots, then removes LightRAG domain. | Deprecate `permanent=true`; keep only archive through route. Make purge the only permanent deletion path after preview/confirmation. | High if removed abruptly. | M |
| `remove(permanent=false)` vs archive terminology | Naming drift | `LightRAGDomainService.remove(permanent=False)` returns archived response | Public DELETE route means archive by default. | HTTP DELETE can be acceptable for archive; existing clients may expect it. | In UI label as “Archive”. In docs describe DELETE default as archive. Avoid “delete” wording for reversible archive. | Low | XS |
| Domain state in manifest vs lifecycle table | State ownership drift | `LightRAGDomain.status/is_healthy`, `LightRAGDomainLifecycleRepository`, `LightRAGDomainRegistry.validate_available()` | Manifest tracks `status`; lifecycle tracks active/blocked states; registry filters blocked IDs and unavailable statuses. | Manifest is runtime/config snapshot; lifecycle table captures operations like archiving/purging. | Document source-of-truth model. Keep both but clarify: manifest = config/runtime reachability; lifecycle table = user-visible operation state. Add helper to compute display status. | Medium | S/M |
| Docker health/reachability vs manifest status | State duplication | `LightRAGReachabilityService`, `_persist_domain_health`, `_persist_started_domain_health` | Health probe writes manifest status and frontend reads status/is_healthy. | Persisting last-known status is useful. | Treat probe as ephemeral source; manifest stores last known. Avoid adding third frontend state model. | Low | S |
| `DocumentService._normalize_lightrag_failure_message` duplicated in `LightRAGIngestionService` | Utility duplication | `app/services/document_service.py`, `app/services/lightrag_ingestion_service.py` | Same regex and missing-secret normalization logic appears in both services. | Both need identical behavior in different flows. | Extract `app/services/lightrag_failure_normalizer.py` with `normalize_lightrag_failure_message()`. Add tests once. | Low | S |
| Document status vs job status vs LightRAG metadata status | Status ownership overlap | `documents.py`, `jobs.py`, `DocumentService.refresh_lightrag_status`, `LightRAGIngestionService._apply_remote_status` | Status appears as document status, job status, `document.meta.lightrag.status`, and track status. | They represent different layers: CE document lifecycle, worker execution, remote LightRAG indexing. | Define ownership and aggregation. Do not create a second processing-status system. Add one status response mapper that joins these layers. | Medium | M |
| `ingestion-status` endpoint vs future processing-status | API redundancy risk | `GET /documents/{id}/ingestion-status` | Existing endpoint already hides `track_id` and exposes document/structure status. | It may be too limited for domain-level admin status. | Extend or wrap it into `processing-status`; do not add an unrelated new status contract without migration. | Medium | S/M |
| `client/src/api/lightrag.ts` custom request helper | Frontend API client duplication | `client/src/api/lightrag.ts`, `client/src/lib/api/client.ts` | `lightrag.ts` manually reads token, calls `fetch`, parses errors, and builds URL while shared `apiRequest()` already exists. | Domain-prefixed request helper may be convenient. | Replace manual fetch with `apiRequest()`, or create `apiRequestForDomain(domainId, path)` built on `apiRequest()`. | Low | S |
| API clients split between `client/src/api` and `client/src/lib/api` | Frontend organization drift | `workspace-tree.ts` under `client/src/api`, `retrieve.ts` under `client/src/lib/api`, `lightrag.ts` custom helper | Two API locations make conventions unclear. | Existing imports may be stable. | Adopt rule: `client/src/api/*` for backend surfaces; keep `client/src/lib/api/client.ts` only for base request primitives. Migrate gradually. | Low | M |
| LightRagDomain frontend type drift | Schema/type drift | `client/src/types/chat.ts` vs `/lightrag/domains` route | Frontend type uses `domain_id`, `workspace`, `port`, `service`, `base_url`; route returns `id`, `display_name`, `host_port`, `status`, `is_healthy`, `retrieval_defaults`. | Another adapter may transform it elsewhere. | Add `LightRagDomainSummary` frontend type matching API; avoid reusing chat-domain type for admin/runtime domain objects. | Medium | S |
| Visual asset type duplication | Schema/type drift | `RetrieveAsset`, `WorkspaceContextAsset`, `ContextPanelItem` asset fields, `AssetCardModel` | Multiple shapes represent the same renderable table/figure/image concept. | Different surfaces need some fields. | Introduce shared frontend `VisualAsset` and map backend response shapes into it at API boundaries. Keep `AssetCardModel` as view model if needed. | Medium | M |
| Source context partial integration | Incomplete route/client risk | `main.py` includes `workspace_tree` but no `workspace_context`; frontend store/types mention source navigator | If source context route/client is missing locally, UI state exists without API surface. | It may be implemented on a branch not visible in raw file. | Ensure one backend source-context route exists and one frontend client. Do not assemble source context in frontend. | Medium | S |
| CLI/TUI active surface | Legacy/parallel UX risk | README documents `context-engine` / `context-tui`; tests include many `test_cli_*` files | CLI/TUI can preserve old API assumptions and slow lean WebUI work. | README says terminal UI is supported local workflow, so it is not dead code. | Keep, but isolate CLI API client from WebUI clients and mark compatibility expectations. Do not let CLI drive new frontend architecture. | Low/Medium | S |
| Graph proxy routes | Backend proxy surface risk | `app/api/routes/lightrag.py`, `client/src/api/lightrag.ts` | Backend proxies LightRAG graph endpoints. | This is intentional: frontend still calls Context Engine, not LightRAG directly. | Keep. Rename comments/docs to “backend LightRAG graph proxy” to avoid direct-boundary confusion. | Low | XS |

---

## 3. LightRAG Domain Lifecycle Decision Matrix

| Operation | Keep public API? | Keep service method? | Make private helper? | Hide from normal admin UI? | Replace with | Notes |
|---|---:|---:|---:|---:|---|---|
| `create` | Yes | Yes | No | No | n/a | Keep as domain creation. Clarify `start` option semantics. |
| `up` | Yes | Yes | Shared helpers for prepare/build/status | No | Start domain | Keep as Start. Should not reprovision more than necessary unless current behavior requires it. |
| `down` | Yes | Yes | Shared status persistence | No | Stop domain | Keep as Stop. |
| `recreate` | Temporarily yes | Maybe | Yes, mostly internal | Yes | Repair domain | Keep compatibility route; demote from normal UI. |
| `repair` | Yes | Yes | Uses shared helpers | No | Main recovery action | Public recovery/superset action. |
| `regenerate` | Temporarily yes / advanced only | Yes | Mostly yes | Yes | Repair or internal maintenance | Not a normal lifecycle action. |
| `remove/archive` | Yes | Yes | Archive helper | No | Archive domain | Default deletion route should be labeled archive in UI. |
| `remove permanent` | Deprecated compatibility only | Yes only if purge uses it internally | Yes | Yes | Purge domain | Dangerous if exposed because it does not clean all CE artifacts. |
| `purge-preview` | Yes | Yes | No | No | n/a | Mandatory before purge. |
| `purge` | Yes | Yes | No | No, but gated | n/a | Only full permanent delete path. Requires confirmation. |

---

## 4. Current State Ownership Map

| State Source | What it should own | Current risk | Target ownership rule |
|---|---|---|---|
| Domain manifest | Domain config snapshot, runtime URLs, host/container ports, embedding snapshot/lock, last-known runtime status | Status/is_healthy may be treated as authoritative live state | Manifest stores config + last-known operational status only. |
| Lifecycle table | User-visible operation state: active, archiving, purging, archived, purged, failed | Overlap with manifest status can confuse availability | Lifecycle table decides whether domain is blocked/hidden during destructive operations. |
| Docker / health probe | Ephemeral truth about container and endpoint health | Probe results persist into manifest, making stale status possible | Probe is live evidence; manifest stores last-known summary with timestamp. |
| Document row status | Context Engine document lifecycle: indexing, ready, failed, deleted | May duplicate LightRAG remote status | Document status is the app-level readable status. |
| Job row status | Worker execution: queued, running, succeeded, failed, canceled | Users may confuse job success with remote indexing success | Job status is execution status only. |
| `document.meta.lightrag` | Remote correlation and remote indexing summary | Raw LightRAG fields may leak or drift | Backend-only correlation (`track_id` private); expose normalized status only. |
| Frontend status | Derived display only | May become a new source of truth | Frontend never owns lifecycle/status truth. It displays backend contracts. |

---

## 5. Proposed Lean Target Model

### 5.1 Admin-facing domain actions

Expose only these normal UI actions:

1. Create
2. Start
3. Stop
4. Repair
5. Archive
6. Preview purge
7. Purge

Hide these from normal UI:

- Recreate
- Regenerate
- Permanent delete query parameter

Keep hidden/backend compatibility temporarily, with deprecation warnings in docs/tests.

### 5.2 Internal lifecycle primitive helpers

Refactor `LightRAGDomainService` around private helpers:

```python
_prepare_domain_runtime(domain_id) -> LightRAGDomain
    - get domain
    - ensure postgres identity
    - provision postgres
    - write env
    - write compose

_build_service(domain) -> LightRAGDomainOperationResult | None
    - runner.build
    - persist error if failed

_recreate_service(domain, operation_name) -> LightRAGDomainOperationResult
    - runner.recreate
    - returns operation result

_probe_and_persist(domain, reachability, attempts, sleep_seconds) -> LightRAGDomain
    - reachability probe
    - persist running/unhealthy/healthy
```

Then:

- `up()` = prepare + build + runner.up + probe/persist
- `recreate()` = prepare + build + recreate + probe/persist
- `repair()` = prepare + build + recreate + probe/persist + repair response
- `regenerate()` = prepare only, no public UX emphasis

### 5.3 Deletion model

- `archive` moves domain root to deleted/archive root and removes active manifest entry.
- `purge-preview` calculates all destructive effects.
- `purge` deletes Context Engine documents, uploads, assets/tables/thumbnails, processing rows, job references, archived domain roots, and LightRAG domain root.
- `permanent=true` on DELETE should become deprecated and eventually blocked or redirected to explicit purge flow.

### 5.4 Status model

Do not add another status system. Create one normalized mapper that joins:

- document row status
- job row status
- `document.meta.lightrag.status`
- LightRAG track status, if present
- domain lifecycle/manifest status, if needed

Output stable contracts such as:

```python
class DocumentProcessingStatusResponse(BaseModel):
    document_id: str
    domain_id: str | None
    job_id: str | None
    document_status: str
    job_status: str | None
    remote_status: str | None
    display_status: Literal[
        "queued", "processing", "indexed", "failed", "cancelled", "unknown"
    ]
    message: str | None
    error_message: str | None
    has_structure: bool
    has_assets: bool
    chunks_count: int | None
    updated_at: datetime | None
```

---

## 6. Implementation Plan

### Phase 0 — Local Verification and Inventory

Owner: coding agent  
Patch size: no code changes

Run:

```bash
python -m pytest -q
cd client && npm run lint && npm run build
rg -n "recreate|repair|regenerate|purge|remove\(|permanent|up_domain|down_domain" app tests client scripts docs
rg -n "LightRAGDomainService|DomainPurgeService|LightRAGDomainLifecycleService|LightRAGDomainRegistry" app tests
rg -n "status-poller|refresh_pending_lightrag_statuses|ingestion-status|track_id|pipeline_status|status_counts" app tests client
rg -n "apiRequest|resolveApiBase|fetch\(|/lightrag/domains|/admin/lightrag/domains" client/src
rg -n "ContextStream|SourceNavigator|WorkspaceTree|AssetCards|sourceContext|contextByAssistantId" client/src
rg -n "deprecated|legacy|context-tui|context-engine|cli" .
```

Deliverable:

- Save raw outputs to `docs/reviews/redundancy-hunt-rg-output.md`.
- Record pre-existing failures before patching.

Acceptance:

- No code changed.
- Baseline test/build status recorded.

---

### Phase 1 — Clarify Lifecycle Semantics Without Behavior Change

Owner: junior dev  
Patch size: XS/S

Tasks:

1. Add docstrings/comments in `app/api/routes/lightrag_admin.py` and `app/lightrag_deploy/service.py` explaining:
   - `repair` = full recovery operation.
   - `recreate` = compatibility/advanced docker recreate operation.
   - `regenerate` = maintenance artifact regeneration.
   - `DELETE permanent=true` = deprecated; use purge flow.
2. Add API docs metadata if FastAPI decorators support it:
   - mark `recreate`, `regenerate`, and `permanent=true` behavior as advanced/deprecated in descriptions.
3. Do not remove routes yet.

Acceptance:

- No behavior changes.
- Existing tests pass.
- Admin route docs make semantics explicit.

---

### Phase 2 — Hide Redundant Actions from Normal Admin UI

Owner: frontend junior dev  
Patch size: S

Tasks:

1. Find admin/settings LightRAG domain lifecycle UI.
2. Ensure normal UI shows only:
   - Start
   - Stop
   - Repair
   - Archive
   - Preview purge
   - Purge
3. Hide or tuck these behind advanced/dev-only UI if currently shown:
   - Recreate
   - Regenerate
   - Permanent delete without preview
4. Ensure destructive purge requires explicit confirmation and uses preview first.

Acceptance:

- No backend route removed.
- UI has fewer lifecycle actions.
- Existing admin workflows still work.
- Frontend build passes.

---

### Phase 3 — Consolidate LightRAGDomainService Private Runtime Helpers

Owner: coding agent  
Patch size: M

Tasks:

Refactor `app/lightrag_deploy/service.py` only internally.

Extract helpers:

```python
_prepare_runtime_artifacts(domain: LightRAGDomain) -> tuple[LightRAGDomain, Any | None]
_build_or_persist_failure(domain, operation: str) -> LightRAGDomainOperationResult | None
_run_and_persist_health(domain, operation: str, command: CommandResult, ...) -> LightRAGDomainOperationResult
```

Rules:

- Preserve public method signatures.
- Preserve response models.
- Preserve exact route behavior.
- Preserve audit event calls in routes.
- Do not change destructive behavior.

Tests to run/update:

```bash
python -m pytest tests/test_lightrag_deploy_service.py tests/test_lightrag_deploy_manifest_compose.py tests/test_lightrag_reachability_service.py -q
```

Acceptance:

- `up`, `recreate`, and `repair` share runtime preparation logic.
- `repair` still returns `LightRAGDomainRepairResult`.
- `recreate` still returns `LightRAGDomainOperationResult`.
- Test coverage confirms behavior unchanged.

---

### Phase 4 — Deprecate Permanent Delete Query Path in Favor of Purge

Owner: senior dev / coding agent  
Patch size: M

Tasks:

1. Keep `DELETE /admin/lightrag/domains/{id}` for archive.
2. For `permanent=true`, either:
   - return `400` with message: “Permanent delete via query parameter is deprecated; use `/purge-preview` then `/purge`”, or
   - keep behavior behind a compatibility setting, but hide from UI and mark deprecated.
3. Ensure `DomainPurgeService.purge_lightrag_domain()` remains the only normal permanent deletion path.
4. Add tests for:
   - archive path still works
   - permanent query path is deprecated or compatibility-gated
   - purge-preview works
   - purge deletes document rows/artifacts/jobs according to existing behavior

Acceptance:

- No accidental permanent deletion path is exposed in normal UI.
- Permanent deletion has explicit preview/confirm flow.
- Tests prove archive and purge semantics separately.

---

### Phase 5 — Extract LightRAG Failure Normalizer

Owner: junior dev  
Patch size: S

Tasks:

1. Create `app/services/lightrag_failure_normalizer.py`.
2. Move duplicated regex and normalization from:
   - `DocumentService._normalize_lightrag_failure_message`
   - `LightRAGIngestionService._normalize_lightrag_failure_message`
3. Replace both service methods with imported helper or tiny wrapper.
4. Add tests:

```bash
python -m pytest tests/test_lightrag_failure_normalizer.py tests/test_lightrag_ingestion_service.py -q
```

Acceptance:

- One implementation of missing-provider-secret normalization.
- Existing failure messages remain stable.
- No circular imports.

---

### Phase 6 — Normalize Frontend API Client Usage

Owner: frontend junior dev  
Patch size: S/M

Tasks:

1. Replace custom manual `fetch` in `client/src/api/lightrag.ts` with shared `apiRequest()` from `client/src/lib/api/client.ts`.
2. Keep domain prefix helper local:

```ts
function domainPath(domainId: string, path: string) {
  return `/lightrag/domains/${encodeURIComponent(domainId)}${path}`;
}
```

3. Do not change call sites.
4. Standardize future API clients under `client/src/api/*`; keep `client/src/lib/api/client.ts` as primitive only.

Acceptance:

- No duplicated token/header/error parsing in `lightrag.ts`.
- Graph proxy calls still go through Context Engine backend.
- Frontend build/lint passes.

---

### Phase 7 — Stabilize Domain and Asset Types

Owner: coding agent + frontend dev  
Patch size: M

Tasks:

1. Add frontend type matching `/lightrag/domains`:

```ts
export type LightRagDomainSummary = {
  id: string;
  display_name: string;
  host_port: number | null;
  is_healthy: boolean | null;
  is_default: boolean;
  status: string | null;
  retrieval_defaults: RetrievalDefaults;
};
```

2. Avoid using legacy `LightRagDomain` from `chat.ts` for this API.
3. Add shared `VisualAsset` type and map:
   - `RetrieveAsset`
   - `WorkspaceContextAsset`
   - `ContextPanelItem` asset fields
   into `AssetCardModel` through one mapper.
4. Keep `AssetCardModel` as a view model if useful.

Acceptance:

- API response types match backend fields.
- Asset rendering does not require random raw metadata parsing.
- Build/lint passes.

---

### Phase 8 — Source Context Route/Client Completion Check

Owner: coding agent  
Patch size: S if missing

Tasks:

1. Confirm whether `app/api/routes/workspace_context.py` exists locally.
2. Confirm whether `app/main.py` includes it.
3. Confirm whether `client/src/api/source-context.ts` exists locally.
4. If missing, add one route/client that uses existing `WorkspaceContextService`.
5. Do not assemble source context in frontend.

Acceptance:

- Workspace tree clicks pass opaque `node_id`.
- Backend parses/authorizes source context.
- Source Navigator works without retrieval/filter mutation.

---

### Phase 9 — CLI/TUI Isolation Check

Owner: senior dev  
Patch size: S/M

Tasks:

1. Decide if CLI/TUI remains supported. README currently presents it as supported, so do not delete it casually.
2. Ensure CLI has its own client adapter and does not force WebUI API shape.
3. Mark old CLI-only tests if they are preserving deprecated behavior.
4. Add `docs/architecture/cli_boundary.md` explaining CLI vs WebUI boundaries.

Acceptance:

- CLI/TUI does not block WebUI/domain lifecycle simplification.
- No active imports from CLI into app runtime unless intentional.

---

## 7. Patch Sequence for Coding Agent

### PR 1 — Baseline + Semantics Docs

Files likely touched:

- `docs/reviews/redundancy-hunt-rg-output.md`
- `app/api/routes/lightrag_admin.py`
- `app/lightrag_deploy/service.py`
- optional route descriptions/docstrings

Tests:

```bash
python -m pytest -q
```

### PR 2 — Hide/Relabel Admin UI Lifecycle Actions

Files likely touched:

- settings/admin LightRAG domain lifecycle components
- domain action menu/component files
- frontend API types if needed

Tests:

```bash
cd client && npm run lint && npm run build
```

### PR 3 — LightRAGDomainService Helper Consolidation

Files likely touched:

- `app/lightrag_deploy/service.py`
- `tests/test_lightrag_deploy_service.py`

Tests:

```bash
python -m pytest tests/test_lightrag_deploy_service.py tests/test_lightrag_deploy_manifest_compose.py tests/test_lightrag_reachability_service.py -q
```

### PR 4 — Safe Deletion Flow Consolidation

Files likely touched:

- `app/api/routes/lightrag_admin.py`
- `app/services/domain_purge_service.py`
- `tests/test_lightrag_*purge*.py` or new tests

Tests:

```bash
python -m pytest tests/test_lightrag_deploy_service.py tests/test_api.py -q
```

### PR 5 — Shared Failure Normalizer

Files likely touched:

- `app/services/lightrag_failure_normalizer.py`
- `app/services/document_service.py`
- `app/services/lightrag_ingestion_service.py`
- `tests/test_lightrag_failure_normalizer.py`

Tests:

```bash
python -m pytest tests/test_lightrag_ingestion_service.py tests/test_lightrag_failure_normalizer.py -q
```

### PR 6 — Frontend API/Type Cleanup

Files likely touched:

- `client/src/api/lightrag.ts`
- `client/src/types/chat.ts`
- maybe new `client/src/types/lightrag.ts`
- `client/src/components/chat/AssetCards.tsx`

Tests:

```bash
cd client && npm run lint && npm run build
```

---

## 8. Test Plan

### Backend tests to add or update

| Test Area | Required Cases |
|---|---|
| Lifecycle service | `up`, `recreate`, `repair` preserve behavior after helper extraction. |
| Repair vs recreate | `repair` returns provision/health detail; `recreate` remains simple compatibility result. |
| Regenerate | `regenerate` prepares artifacts but does not pretend to be normal start/repair operation. |
| Archive | default DELETE archives and updates lifecycle state. |
| Permanent delete deprecation | `permanent=true` is blocked/deprecated or compatibility-gated. |
| Purge | preview summarizes docs/assets/chunks/uploads; purge cancels jobs, deletes docs/artifacts, removes domain. |
| Failure normalization | missing secret messages normalized consistently from upload, ingestion, and poll refresh paths. |
| Status ownership | document status, job status, and LightRAG metadata map to one stable response. |

### Frontend validation

| Area | Required Cases |
|---|---|
| Domain lifecycle UI | Normal admin actions do not show recreate/regenerate/permanent-delete shortcuts. |
| Graph API client | Uses shared `apiRequest`; no custom token/header/error parsing. |
| Domain types | `/lightrag/domains` consumer expects `id`, not `domain_id`, unless adapter maps it intentionally. |
| Asset cards | Workspace and retrieval assets render through the same card grammar. |
| Source Navigator | Tree click sets source navigator state only; does not trigger retrieval or mutate filters. |

---

## 9. Risks and Guardrails

1. **Do not remove `recreate` immediately.** Keep route compatibility until tests and UI usage are verified.
2. **Do not remove `regenerate` before confirming no scripts/tests rely on it.** Demote first.
3. **Do not merge archive and purge semantics.** Archive is reversible-ish; purge is destructive.
4. **Do not expose `track_id` or raw LightRAG internals to normal frontend status UI.** Existing ingestion-status already strips `track_id`.
5. **Do not let CLI/TUI tests keep stale backend semantics alive silently.** Classify them as supported or legacy.
6. **Do not create a second processing status model.** Add a mapper/aggregator over existing document/job/LightRAG metadata.
7. **Do not let frontend become a source of truth for domain/document status.** It should render backend contracts only.

---

## 10. Definition of Done

The redundancy-reduction pass is done when:

- Normal admin UI exposes only Start, Stop, Repair, Archive, Preview Purge, and Purge.
- `repair`, `recreate`, and `regenerate` are documented and no longer confusing to junior developers.
- Permanent delete query path is deprecated, compatibility-gated, or removed after migration.
- `LightRAGDomainService` has less repeated prepare/build/recreate/probe/persist code.
- Missing-secret failure normalization exists in one helper.
- Frontend `lightrag.ts` uses shared `apiRequest` or an approved wrapper.
- Domain/asset frontend types are aligned with backend contracts.
- Source context remains backend-owned.
- Backend tests and frontend build/lint pass, or pre-existing failures are documented.
