# Cleanup Roadmap

## Phase 0: Safety and baseline

**Goal:** Freeze current behavior before cleanup.

Tasks:

1. Record current branch/commit.
2. Run full backend and frontend tests locally.
3. Generate current route map from FastAPI app.
4. Generate import/reference map for candidate dead files.
5. Add missing smoke tests for lifecycle/status routes before refactor.

Acceptance criteria:

- Current tests pass or failures are documented.
- Route map committed to docs.
- Cleanup branch starts from known baseline.

Risk: Low

## Phase 1: Safe repository hygiene

**Goal:** Remove obvious generated/local artifacts from version control.

Candidate artifacts to verify:

- `.data/uploads/`
- `.vs/`
- `context_engine.egg-info/`
- `__pycache__/`
- `client/tsconfig.tsbuildinfo`
- `migrations/2popups.png`

Acceptance criteria:

- `.gitignore` updated.
- Clean checkout/build/test does not recreate tracked noise.
- No runtime paths changed.

Risk: Low

## Phase 2: Lifecycle terminology cleanup

**Goal:** Make normal admin domain operations understandable.

Tasks:

1. Document canonical operations: create, start, stop, repair, archive, purge-preview, purge.
2. Mark `recreate` as compatibility/advanced.
3. Mark `regenerate` as internal/advanced maintenance.
4. Update frontend labels/tooltips to avoid exposing too many verbs.
5. Add route deprecation comments and tests.

Acceptance criteria:

- Normal UI no longer presents `recreate` and `regenerate` as peer actions to repair.
- API compatibility maintained.

Risk: Medium

## Phase 3: Shared lifecycle implementation path

**Goal:** Reduce duplicated runtime recovery logic.

Tasks:

1. Extract private `_recover_domain_runtime` or equivalent from `repair`/`recreate`.
2. Keep response mapping separate for legacy route compatibility.
3. Add regression tests proving `repair` and `recreate` share core behavior.

Acceptance criteria:

- One core implementation path for artifact refresh + Docker recreate + health persistence.
- Public route behavior unchanged.

Risk: Medium

## Phase 4: State ownership consolidation

**Goal:** Make domain/document/job status semantics explicit.

Tasks:

1. Add status semantics doc.
2. Ensure domain status endpoint distinguishes desired state from runtime health.
3. Ensure document ingestion status distinguishes document status from job attempt status.
4. Ensure frontend uses backend status projections directly.

Acceptance criteria:

- No UI-only invented backend statuses unless explicitly mapped.
- Status tests cover stale/unreachable/failed states.

Risk: Medium

## Phase 5: Split high-entropy service internals

**Goal:** Make `LightRAGDomainService` easier to maintain without breaking API behavior.

Recommended extraction order:

1. Artifact generation helper/service.
2. Runtime Docker helper/service.
3. Health probing/status persistence helper/service.
4. Postgres provisioning wrapper if needed.

Acceptance criteria:

- Public facade remains stable.
- Each extracted unit has a narrow responsibility.
- No abstract interfaces unless multiple implementations exist.

Risk: Medium/High

## Phase 6: Frontend simplification

**Goal:** Reduce duplicated API/polling/UI status logic.

Tasks:

1. Audit `client/src/api` for duplicate fetch logic.
2. Audit hooks for duplicate polling.
3. Create one domain status hook and one document ingestion status hook.
4. Ensure context panel/source navigation consume one canonical evidence/source shape.
5. Consolidate repeated cards/tables only where it reduces mental overhead.

Acceptance criteria:

- Components are thinner.
- Backend contract types are centralized.
- Polling behavior is not duplicated across components.

Risk: Medium

## Phase 7: Contract hardening

**Goal:** Stabilize schemas before future feature work.

Tasks:

1. Freeze Evidence contract.
2. Freeze document status response contract.
3. Freeze domain lifecycle response contract.
4. Add schema tests and frontend type alignment.

Acceptance criteria:

- UI changes for context panel/images/tables can happen without route churn.

Risk: Medium
