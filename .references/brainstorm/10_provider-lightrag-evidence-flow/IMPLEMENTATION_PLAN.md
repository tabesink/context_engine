# Implementation Plan for Junior Developer

## Phase 0: Confirm Current Architecture and Failing Tests

**Goal:** Establish baseline.

**Steps:**

1. Pull latest repo.
2. Run backend tests.
3. Run frontend tests/lint/build.
4. Confirm current route list.
5. Confirm chat API behavior.
6. Confirm LightRAG domain creation/upload/retrieve smoke path.

**Acceptance Criteria:**

- Current failures documented.
- No implementation begins before baseline is known.

## Phase 1: Rename Settings Route to Provider

**Goal:** Replace `ai-models` / `LLM Model` concept with `provider`.

**Likely files:**

```text
client/src/stores/settings-dialog-store.ts
client/src/app/settings/*
client/src/components/*settings*
client/src/components/chat/ChatComposer.tsx
```

**Acceptance Criteria:**

- UI displays `Provider` route.
- Route key is `provider`.
- Admin guard remains.
- No references to old `LLM Model` route remain except migration notes.

## Phase 2: Add Backend Provider Profile Model and Admin APIs

**Goal:** Make provider configuration first-class.

**Likely files:**

```text
app/api/routes/providers_admin.py
app/services/provider_profile_service.py
app/storage/tables.py
app/storage/repositories/provider_profile_repository.py
app/schemas/provider.py
app/main.py
alembic/versions/*
```

**Acceptance Criteria:**

- Admin can list/create/update provider profiles.
- Regular users are forbidden.
- API key responses are masked.
- Env-managed default profile can be represented if desired.

## Phase 3: Secure API Key Handling

**Goal:** Prevent credential leakage.

**Acceptance Criteria:**

- No raw API key in API response.
- No raw API key in logs.
- Tests prove redaction.
- Storage strategy documented.

## Phase 4: Link Provider Profile to LightRAG Domain

**Goal:** Domain knows which provider/model settings it uses.

**Likely files:**

```text
app/lightrag_deploy/models.py
app/lightrag_deploy/service.py
app/lightrag_deploy/compose.py
app/services/lightrag_domain_service.py
app/services/lightrag_domain_registry.py
```

**Acceptance Criteria:**

- Domain creation accepts provider profile and embedding model.
- Generated domain env uses selected provider profile.
- Existing domains have safe migration/default behavior.

## Phase 5: Enforce Embedding Model Lock

**Goal:** Prevent mixed embeddings in one domain.

**Acceptance Criteria:**

- Domain locks embedding config after first successful ingestion.
- Embedding model/dim changes blocked after lock.
- Reindex/rebuild is the only explicit escape path.

## Phase 6: Validate Admin Upload → Ingestion Flow

**Goal:** Guarantee upload lands in correct local + LightRAG stores.

**Acceptance Criteria:**

- Upload requires valid domain.
- Upload validates provider configured.
- Upload stores document-domain-embedding metadata.
- Ingestion sends chunks to selected domain.
- Failure states are visible and retryable.

## Phase 7: Validate User Chat → `/retrieve` Flow

**Goal:** Make chat use Context Engine canonical retrieval.

**Acceptance Criteria:**

- Chat submits selected domain ID to backend.
- Chat calls `/retrieve` directly or streaming wrapper around RetrievalService.
- Regular users can retrieve.
- Evidence response is mapped to UI.

## Phase 8: Stabilize Evidence Contract

**Goal:** Context panel can render stable citations.

**Acceptance Criteria:**

- Evidence includes document/source/chunk/page/reference fields.
- Assets are included when requested.
- Frontend adapter maps backend evidence to context items.

## Phase 9: Wire Workspace Tree

**Goal:** Domain tree comes from backend workspace-tree endpoint.

**Acceptance Criteria:**

- Tree fetches by selected domain ID.
- Tree renders documents/sections/pages/assets.
- Evidence can highlight/link to tree nodes.

## Phase 10: Add Tests and Docs

**Goal:** Lock down behavior.

**Acceptance Criteria:**

- Backend provider/domain/upload/retrieve tests added.
- Frontend settings/chat/context/tree tests added.
- ADRs written.
- README/setup docs updated.
