# Context Engine — Redundancy Hunt / Leaner Codebase Prompt

You are a senior software architect, full-stack developer, and codebase reviewer working on:

`https://github.com/tabesink/context_engine.git`

The codebase has recently been modified several times. Your task is **not** to add a new feature. Your task is to identify redundant APIs, overlapping functions, duplicated services, stale code, duplicate frontend state, and contract drift so the codebase can become leaner before the next implementation pass.

## Primary Goal

Find redundancy candidates and produce a safe deletion / consolidation plan.

You must distinguish between:

1. **Truly redundant** — can likely be removed or merged.
2. **Overlapping but intentionally distinct** — keep, but clarify naming/docs.
3. **Overlapping implementation detail** — keep public behavior, consolidate internals.
4. **Legacy/deprecated** — isolate, mark, or schedule removal.
5. **Not redundant** — appears similar but serves a separate lifecycle/security purpose.

Do not make broad rewrites. Do not delete code blindly. Do not change behavior unless tests prove compatibility.

## High-Priority Suspicion

Start with this question:

**Are `recreate`, `repair`, `regenerate`, `up`, `down`, `remove`, `purge-preview`, and `purge` all necessary as public/admin API operations, or are some of them redundant UI/API concepts around the same underlying lifecycle primitives?**

In particular, inspect whether:

* `repair` is a superset of `recreate`
* `regenerate` is only an internal helper and should not be a public operation
* `create_domain(start=true)` calls `repair`, creating unclear semantics
* `remove(permanent=true)` overlaps with `/purge`
* `delete?permanent=true`, `/purge-preview`, and `/purge` create too many destructive paths
* `up`, `down`, `recreate`, and `repair` share docker/compose/status-persistence behavior that should become shared private helpers
* admin-facing UI should expose fewer lifecycle actions than the backend supports internally

Do **not** assume these are redundant. Prove it from code paths, tests, and actual semantics.

## Required Search Passes

Run these searches and include findings:

```bash
rg -n "recreate|repair|regenerate|purge|remove\(|permanent|up_domain|down_domain" app tests client scripts docs
rg -n "LightRAGDomainService|DomainPurgeService|LightRAGDomainLifecycleService|LightRAGDomainRegistry" app tests
rg -n "status-poller|refresh_pending_lightrag_statuses|ingestion-status|track_id|pipeline_status|status_counts" app tests client
rg -n "apiRequest|resolveApiBase|fetch\(|/lightrag/domains|/admin/lightrag/domains" client/src
rg -n "ContextStream|SourceNavigator|WorkspaceTree|AssetCards|sourceContext|contextByAssistantId" client/src
rg -n "deprecated|legacy|context-tui|context-engine|cli" .
```

## Redundancy Candidate Classes to Fetch

### A. Public API Surface Redundancy

Look for admin/user routes that expose too many operations for the same lifecycle concept.

Examples to verify:

* `POST /admin/lightrag/domains/{domain_id}/recreate`
* `POST /admin/lightrag/domains/{domain_id}/repair`
* `POST /admin/lightrag/domains/{domain_id}/regenerate`
* `DELETE /admin/lightrag/domains/{domain_id}?permanent=true`
* `DELETE /admin/lightrag/domains/{domain_id}/purge`
* `POST /admin/lightrag/domains/{domain_id}/purge-preview`

For each route, document:

| Route | User-facing meaning | Internal service method | Side effects | Overlap | Keep / Merge / Hide / Delete | Test impact |
| ----- | ------------------- | ----------------------- | ------------ | ------- | ---------------------------- | ----------- |

### B. Service Method Redundancy

Inspect whether service methods have shared internals that should be private primitives.

Focus on:

* docker compose generation
* env file generation
* postgres provisioning
* container recreation
* reachability/health probing
* status persistence
* lifecycle-state writes
* audit logging

### C. Domain State Redundancy

Inspect whether the code tracks the same domain state in too many places:

* manifest domain `status`
* manifest `is_healthy`
* lifecycle table state
* Docker container state
* LightRAG health/reachability
* frontend status badge state

Create one proposed source-of-truth model:

* **Manifest**: static/runtime config snapshot
* **Lifecycle table**: user-visible lifecycle state such as active/archiving/purging/archived/failed
* **Docker/health probe**: ephemeral operational state
* **Frontend**: derived display state only

### D. Document / Job / LightRAG Status Redundancy

Inspect overlap between:

* document `status`
* job `status`
* `/documents/{document_id}/ingestion-status`
* `/jobs`
* status poller
* LightRAG `track_id` metadata
* domain processing status, if present

Goal: avoid a second document-processing status system.

### E. Frontend API Client Redundancy

Check whether API clients are split between `client/src/api` and `client/src/lib/api`, and whether multiple helpers build the same base URL/token headers.

### F. Right Panel / Source Navigation Redundancy

Confirm:

* one right-panel shell
* two views only: Context Stream and Source Navigator
* one `AssetCards` visual grammar
* tree clicks do not trigger retrieval
* source clicks do not mutate retrieval filters
* frontend passes opaque `node_id`; backend parses it

### G. Schema / Type Drift

Compare backend schemas and frontend types for:

* `Evidence`
* visual assets
* workspace tree nodes
* workspace source context
* document status
* job status
* LightRAG domain summaries

### H. Legacy / Dead Code

Identify code that is deprecated or no longer part of active workflow.

Focus on:

* CLI/TUI code
* old deployment scripts
* old env overlays
* old docs that contradict current startup/deployment path
* tests that preserve deprecated behavior unnecessarily

## Output Deliverable 1 — Redundancy Inventory

Create this table:

| Candidate | Category | Evidence / Files | Why It Looks Redundant | Why It Might Not Be | Recommendation | Risk | Patch Size |
| --------- | -------- | ---------------- | ---------------------- | ------------------- | -------------- | ---- | ---------- |

Patch size:

* **XS**: rename, docs, hide UI action, delete dead import
* **S**: consolidate helper or route wrapper, tests required
* **M**: merge public API routes with compatibility shim, tests required
* **L**: larger redesign; document only, do not implement now

## Output Deliverable 2 — Lifecycle Operation Decision Matrix

For LightRAG domain lifecycle operations, produce:

| Operation | Keep as public API? | Keep as service method? | Make private helper? | Hide from UI? | Replace with | Notes |
| --------- | ------------------: | ----------------------: | -------------------: | ------------: | ------------ | ----- |

Must include:

* `create`
* `up`
* `down`
* `recreate`
* `repair`
* `regenerate`
* `remove/archive`
* `remove permanent`
* `purge-preview`
* `purge`

## Output Deliverable 3 — Proposed Lean Lifecycle Model

Define the smallest set of admin-facing domain actions.

Suggested starting point to evaluate:

* `Create domain`
* `Start domain`
* `Stop domain`
* `Repair domain`
* `Archive domain`
* `Preview purge`
* `Purge domain`

Then decide whether `Recreate` and `Regenerate` should become internal implementation details under `Repair`, or remain available only as advanced/dev-only operations.

Also decide whether `DELETE /admin/lightrag/domains/{domain_id}?permanent=true` should be removed/deprecated in favor of explicit `/purge-preview` + `/purge` safety flow.

## Output Deliverable 4 — Patch Plan

Create a phased lean refactor plan.

### Phase 0 — Safety Baseline

* Run backend tests.
* Run frontend lint/build.
* Record pre-existing failures.
* List routes and public API clients before changes.

### Phase 1 — No-Behavior Cleanup

* Rename ambiguous UI labels if needed.
* Add comments/docstrings clarifying operation differences.
* Consolidate repeated private helpers.
* Mark deprecated operations as advanced/internal where appropriate.

### Phase 2 — API Surface Simplification

* Keep compatibility routes if needed.
* Internally route duplicate public endpoints to one implementation.
* Add deprecation metadata/docs for redundant endpoints instead of breaking clients immediately.
* Remove frontend buttons for redundant/advanced operations before removing backend routes.

### Phase 3 — State/Status Simplification

* Define source of truth for domain state.
* Normalize document/job/status ownership.
* Prevent duplicate frontend polling loops.

### Phase 4 — Tests

Add targeted tests for:

* route compatibility
* lifecycle transitions
* repair/recreate/regenerate behavior boundaries
* purge vs archive behavior
* admin-only authorization
* user-readable domain list remains safe
* frontend build/lint

## Output Deliverable 5 — Safe Patches

Only implement XS/S patches unless explicitly approved.

Preferred small patches:

1. Extract shared private lifecycle helpers if duplication is obvious.
2. Hide or relabel redundant frontend actions without removing backend compatibility.
3. Add deprecation notes/docs for public routes that should be removed later.
4. Consolidate duplicated API request helpers.
5. Consolidate duplicated status display chips/cards.
6. Isolate deprecated CLI/TUI code from active app imports.

Do not:

* delete destructive routes without migration/deprecation plan
* remove tests before replacing coverage
* merge `repair` and `recreate` if they have materially different side effects
* expose LightRAG directly to frontend
* create a second domain status model

## Final Report Format

Use this exact structure:

```md
# Context Engine Redundancy Hunt Review

## 1. Executive Summary

## 2. Redundancy Inventory

## 3. LightRAG Domain Lifecycle Decision Matrix

## 4. Current State Ownership Map

## 5. Proposed Lean Target Model

## 6. Patch Plan

## 7. Patches Implemented

## 8. Tests Run and Results

## 9. Remaining Redundancy / Deferred Deletions

## 10. Recommended Next Steps
```

## Acceptance Criteria

The review is acceptable only if:

* each redundancy claim includes file/function/route evidence
* `repair` vs `recreate` vs `regenerate` are explicitly compared
* archive/delete/purge semantics are explicitly compared
* admin UI actions are separated from backend compatibility routes
* domain state source-of-truth is clarified
* document/job/status ownership is clarified
* frontend API/client duplication is checked
* legacy CLI/TUI impact is checked
* no destructive code removal is performed without a migration/deprecation plan
* final recommendations reduce entropy without breaking current workflows
