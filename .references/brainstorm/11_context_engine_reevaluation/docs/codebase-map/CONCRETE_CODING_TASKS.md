# Concrete Coding Tasks

## Task 1: Fix Settings Route Type

**Goal:** Align frontend route state with `Provider`.

**Files likely affected:**

```text
client/src/stores/settings-dialog-store.ts
client/src/components/settings/SettingsDialog.tsx
```

**Steps:**

1. Replace `ai-models` route id with `provider`.
2. Verify any saved state/default route references.
3. Run TypeScript check.

**Acceptance criteria:**

- Settings opens Provider route without type errors.
- No visible "LLM Model" route label remains.

**Tests:**

- Frontend unit or type test.
- Manual settings navigation.

**Risk:** Low

---

## Task 2: Add AI Settings Alembic Migration

**Goal:** Create runtime schema for AI settings.

**Files likely affected:**

```text
migrations/alembic/versions/*
app/storage/tables.py
```

**Steps:**

1. Add migration for AI model profile/settings/secret tables.
2. Add indexes/constraints.
3. Run `alembic upgrade head` on fresh DB.
4. Run admin AI settings tests.

**Acceptance criteria:**

- Fresh DB has required tables.
- `/admin/ai-settings` does not fail due missing table.

**Tests:**

- Migration smoke test.
- API settings test.

**Risk:** Medium

---

## Task 3: Pass Secret Repository into LightRAG Domain Service

**Goal:** Make UI-saved provider keys available to LightRAG env generation.

**Files likely affected:**

```text
app/api/routes/lightrag_admin.py
app/services/model_profile_resolver.py
app/services/ai_model_settings_service.py
```

**Steps:**

1. Construct `AIProviderSecretRepository` with `SecretCryptoService`.
2. Pass it into `AIModelSettingsService`.
3. Ensure `ModelProfileResolver.get_provider_secret_value()` can decrypt DB secret.
4. Add tests.

**Acceptance criteria:**

- API key entered in settings is injected into domain env generation.
- Raw secret is not logged or returned.

**Tests:**

- Domain env generation uses DB secret.
- Missing secret gives clear error.
- Ollama can skip secret if expected.

**Risk:** Medium

---

## Task 4: Implement Real Provider Test or Rename It

**Goal:** Avoid false "connection passed" behavior.

**Files likely affected:**

```text
app/services/ai_model_settings_service.py
client/src/components/settings/panels/AIModelSettingsPanel.tsx
```

**Option A: Low entropy**

Rename UI/action to "Validate configuration" and explain that it checks required config only.

**Option B: Better functionality**

Perform a minimal provider call.

**Acceptance criteria:**

- UI wording matches behavior.
- Failure messages are useful.

**Risk:** Medium

---

## Task 5: Persist Document Domain Column

**Goal:** Align document rows with domain-aware retrieval/workspace tree.

**Files likely affected:**

```text
app/storage/repositories/documents.py
app/services/document_service.py
app/storage/tables.py
migrations/alembic/versions/*
```

**Steps:**

1. Ensure migration creates `documents.lightrag_domain_id`.
2. Change repository create method to accept and persist it.
3. Backfill from metadata if needed.
4. Prefer column in domain filtering where safe.

**Acceptance criteria:**

- Uploaded document row has `lightrag_domain_id`.
- Metadata remains backward compatible.
- Workspace tree still works.

**Risk:** Medium

---

## Task 6: Enforce Embedding Fingerprint on Ingestion

**Goal:** Prevent mixed embeddings in a LightRAG domain.

**Files likely affected:**

```text
app/lightrag_deploy/models.py
app/lightrag_deploy/service.py
app/services/lightrag_ingestion_service.py
app/services/document_service.py
```

**Steps:**

1. Read domain embedding snapshot/fingerprint.
2. Store fingerprint on document at upload or ingestion.
3. Reject mismatch.
4. Add tests.

**Acceptance criteria:**

- Existing non-empty domain cannot change embedding model silently.
- Ingestion stores embedding identity.

**Risk:** Medium

---

## Task 7: Map Retrieve Evidence to Context Panel

**Goal:** Populate right-side evidence panel from `/retrieve`.

**Files likely affected:**

```text
client/src/lib/lightrag-client.ts
client/src/components/chat/LightRagChatShell.tsx
client/src/components/chat/SidePanel.tsx
```

**Steps:**

1. Preserve raw `/retrieve` response.
2. Map evidence into `ContextItem`.
3. Map assets into context item assets.
4. Call context update handler.
5. Add empty-state handling.

**Acceptance criteria:**

- Evidence appears in context panel after question.
- Citation/source fields render.
- No evidence shows graceful message.

**Risk:** Medium

---

## Task 8: Fetch Workspace Tree for Selected Domain

**Goal:** Populate workspace tree from backend.

**Files likely affected:**

```text
client/src/lib/api/workspace-tree.ts
client/src/components/chat/LightRagChatShell.tsx
client/src/components/chat/WorkspaceTree.tsx
```

**Steps:**

1. Add/verify workspace tree API client.
2. Fetch tree on domain selection.
3. Refetch after upload/reingestion if frontend supports upload.
4. Optionally highlight nodes from evidence references.

**Acceptance criteria:**

- Tree shows domain/document/section/page/chunk/assets.
- Regular users can view tree.
- Admin-only not required.

**Risk:** Medium
