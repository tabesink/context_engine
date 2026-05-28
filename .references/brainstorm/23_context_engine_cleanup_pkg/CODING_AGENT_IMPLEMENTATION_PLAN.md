# Coding Agent Implementation Plan

Use these tasks one at a time. Do not combine high-risk lifecycle refactors with unrelated UI cleanup.

## Task 1: Verify and remove generated repository artifacts

**Goal:** Remove committed local/generated files that increase repo entropy.

**Files likely affected:**

- `.gitignore`
- `.data/uploads/`
- `.vs/`
- `context_engine.egg-info/`
- `__pycache__/`
- `client/tsconfig.tsbuildinfo`
- `migrations/2popups.png`

**Do not touch:** Runtime storage path logic.

**Steps:**

1. Run `git ls-files` for each candidate.
2. If tracked and not intentionally versioned, remove with `git rm -r --cached` or `git rm` as appropriate.
3. Update `.gitignore`.
4. Run backend/frontend tests or minimum import/build checks.

**Acceptance criteria:**

- Generated artifacts are not tracked.
- New builds do not dirty `git status`.
- No application code changed.

**Tests:** Build/test smoke.

**Rollback plan:** Restore removed files from git if any were required.

**Risk:** Low

---

## Task 2: Add lifecycle operation semantics documentation

**Goal:** Document which LightRAG domain operations are canonical, advanced, compatibility, or dangerous.

**Files likely affected:**

- `docs/lightrag-domain-lifecycle.md` or existing docs folder.
- `app/api/routes/lightrag_admin.py` comments/docstrings only.

**Do not touch:** Route behavior.

**Steps:**

1. Document `create`, `start/up`, `stop/down`, `repair`, `archive`, `purge-preview`, `purge` as canonical/admin operations.
2. Document `recreate` as compatibility/advanced.
3. Document `regenerate` as internal/advanced maintenance.
4. Document destructive operation confirmation requirements.

**Acceptance criteria:**

- Junior developer can explain which operation to call for normal recovery.
- No runtime behavior changed.

**Tests:** Not required beyond docs lint if present.

**Rollback plan:** Revert docs only.

**Risk:** Low

---

## Task 3: Hide `recreate` and `regenerate` from normal frontend/admin UX

**Goal:** Reduce admin surface confusion while preserving backend compatibility.

**Files likely affected:**

- `client/src/api/*lightrag*` or domain API client.
- Domain management components/pages.
- Tests for domain management UI.

**Do not touch:** Backend route implementation.

**Steps:**

1. Locate frontend buttons/actions for `recreate` and `regenerate`.
2. Move them to an advanced/debug section or remove from default UI.
3. Ensure `repair` is the prominent recovery action.
4. Update labels/tooltips to use Start/Stop/Repair/Archive/Purge language.

**Acceptance criteria:**

- Normal admin surface is simpler.
- Compatibility actions remain available only if deliberately exposed.
- No API contract changes.

**Tests:** Frontend interaction/unit tests if present; manual admin domain flow.

**Rollback plan:** Restore previous component layout.

**Risk:** Low/Medium

---

## Task 4: Add tests around `repair`, `recreate`, and `regenerate`

**Goal:** Establish safety before implementation consolidation.

**Files likely affected:**

- `tests/test_lightrag_domain_service.py`
- `tests/test_lightrag_deploy_service.py`
- `tests/test_lightrag_admin_routes.py` or equivalent.

**Do not touch:** Production implementation unless needed for testability.

**Steps:**

1. Test `repair` success path.
2. Test `repair` Docker failure path.
3. Test `recreate` compatibility response.
4. Test `regenerate` does not unexpectedly start/stop runtime.
5. Test audit log behavior if routes perform audits.

**Acceptance criteria:**

- Current behavior is captured.
- Tests fail if repair/recreate diverge unexpectedly.

**Tests:** New backend tests.

**Rollback plan:** Remove tests if they incorrectly encode unintended behavior, then rewrite with verified semantics.

**Risk:** Low/Medium

---

## Task 5: Extract shared private runtime recovery helper

**Goal:** Reduce duplicated logic between `repair` and `recreate`.

**Files likely affected:**

- `app/lightrag_deploy/service.py`
- Lifecycle service tests.

**Do not touch:** Public route paths or response schemas.

**Steps:**

1. Identify repeated steps in `repair` and `recreate`.
2. Extract private helper for artifact refresh + compose write + Docker recreate + health probe/persist.
3. Keep `repair` response rich.
4. Keep `recreate` response compatible.
5. Run lifecycle tests.

**Acceptance criteria:**

- One core implementation path exists.
- Public behavior unchanged.
- Tests pass.

**Tests:** Full LightRAG lifecycle service tests.

**Rollback plan:** Inline helper back into original methods.

**Risk:** Medium

---

## Task 6: Create status semantics document and tests

**Goal:** Clarify domain/document/job status ownership.

**Files likely affected:**

- `docs/status-semantics.md`
- `app/api/routes/documents.py`
- `app/api/routes/jobs.py`
- `app/services/processing_status_service.py`
- `app/services/processing_status_cache.py`
- Tests for processing status routes/services.

**Do not touch:** Database schema in this task.

**Steps:**

1. Document difference between document state, job attempt state, processing progress, domain desired state, and runtime health.
2. Add/adjust tests for failed/stale/running status projections.
3. Ensure status responses include clear enum names and freshness metadata where possible.

**Acceptance criteria:**

- No ambiguous status ownership remains undocumented.
- Tests encode expected projections.

**Tests:** Processing status route/service tests; document ingestion status tests.

**Rollback plan:** Revert doc and test-only changes if they conflict with intended semantics.

**Risk:** Medium

---

## Task 7: Thin document route handlers through a structure read service

**Goal:** Reduce repeated document structure/access loading across document routes.

**Files likely affected:**

- `app/api/routes/documents.py`
- `app/services/document_asset_service.py`
- New or existing service: `document_structure_read_service.py`
- Document navigation tests.

**Do not touch:** Public response schemas unless frontend is updated in same PR.

**Steps:**

1. Identify repeated access policy + repository + structure reconstruction logic.
2. Move repeated read/projection logic into one service.
3. Keep route handlers thin.
4. Preserve all response shapes.

**Acceptance criteria:**

- Route handlers mostly orchestrate auth/dependency/response.
- Structure loading lives in one place.
- Existing document/source navigation tests pass.

**Tests:** Document routes, rich navigation, workspace context tests.

**Rollback plan:** Revert service extraction.

**Risk:** Medium

---

## Task 8: Frontend polling/API consolidation audit

**Goal:** Prevent duplicate UI state and duplicated API call logic.

**Files likely affected:**

- `client/src/api/`
- `client/src/hooks/`
- Domain management components.
- Document/status/context panel components.

**Do not touch:** Backend.

**Steps:**

1. Search for repeated `fetch`, `setInterval`, polling, status enum mapping, and domain/document API calls.
2. Create or reuse one API client per backend concept.
3. Create one polling hook for domain status and one for document ingestion status.
4. Replace component-local polling.

**Acceptance criteria:**

- Status polling logic is centralized.
- Components render status but do not define backend semantics.

**Tests:** Frontend unit/integration tests or manual admin upload/domain flows.

**Rollback plan:** Restore previous component logic.

**Risk:** Medium
