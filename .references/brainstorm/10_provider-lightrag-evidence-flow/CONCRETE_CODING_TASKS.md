# Concrete Coding Tasks

## Task 1: Rename Settings `ai-models` to `provider`

**Goal:** Align UI language with provider configuration.

**Files likely affected:**

```text
client/src/stores/settings-dialog-store.ts
client/src/app/settings/*
client/src/components/*settings*
```

**Steps:**

1. Replace route key `ai-models` with `provider`.
2. Rename visible label to `Provider`.
3. Ensure admin-only guard.
4. Update tests and snapshots.

**Acceptance Criteria:** Settings shows Provider and old route is gone.

**Risk:** Low.

## Task 2: Add ProviderProfile schema/service/repository

**Goal:** Add backend provider profile concept.

**Files likely affected:**

```text
app/schemas/provider.py
app/services/provider_profile_service.py
app/storage/repositories/provider_profile_repository.py
app/storage/tables.py
alembic/versions/*
```

**Acceptance Criteria:** Provider profiles can be persisted or env-managed default profile represented.

**Risk:** Medium.

## Task 3: Add Admin Provider Routes

**Goal:** Admin can manage providers.

**Files likely affected:**

```text
app/api/routes/providers_admin.py
app/main.py
```

**Acceptance Criteria:** CRUD/test endpoints exist and require admin.

**Risk:** Medium.

## Task 4: Add secret redaction tests

**Goal:** Prevent API key leakage.

**Acceptance Criteria:** API responses never contain raw key.

**Risk:** Low.

## Task 5: Link LightRAG domain to provider profile

**Goal:** Domain creation uses provider profile.

**Files likely affected:**

```text
app/lightrag_deploy/models.py
app/lightrag_deploy/service.py
app/lightrag_deploy/compose.py
```

**Acceptance Criteria:** New domain env generated from selected provider.

**Risk:** Medium.

## Task 6: Add embedding model lock

**Goal:** Prevent mixed embeddings.

**Acceptance Criteria:** Existing/non-empty domain cannot silently change embedding model or dimension.

**Risk:** Medium.

## Task 7: Harden upload validation

**Goal:** Upload requires ready domain and configured provider.

**Files likely affected:**

```text
app/services/document_service.py
app/services/lightrag_ingestion_service.py
```

**Acceptance Criteria:** Upload fails early with clear error if domain/provider invalid.

**Risk:** Medium.

## Task 8: Align chat with `/retrieve`

**Goal:** Frontend chat uses Context Engine retrieval.

**Files likely affected:**

```text
client/src/components/chat/LightRagChatShell.tsx
client/src/api/*
client/src/types/chat.ts
```

**Acceptance Criteria:** Chat sends query/domain to `/retrieve` or streaming wrapper around RetrievalService.

**Risk:** High because it affects user-visible chat.

## Task 9: Add RetrieveResponse → ContextPanel adapter

**Goal:** Stable evidence UI.

**Files likely affected:**

```text
client/src/lib/retrieve-response-adapter.ts
client/src/components/chat/SidePanel.tsx
client/src/types/chat.ts
```

**Acceptance Criteria:** Context panel renders document/page/chunk/source references.

**Risk:** Medium.

## Task 10: Wire backend workspace tree endpoint

**Goal:** Workspace tree uses backend corpus structure.

**Files likely affected:**

```text
client/src/components/chat/WorkspaceTree.tsx
client/src/api/workspace-tree.ts
client/src/stores/lightrag-domain-store.ts
```

**Acceptance Criteria:** Tree fetches `/lightrag/domains/{domain_id}/workspace-tree` by selected domain ID.

**Risk:** Medium.
