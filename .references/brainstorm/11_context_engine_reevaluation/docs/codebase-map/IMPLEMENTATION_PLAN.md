# Implementation Plan for Junior Developer

## Phase 0: Confirm Current Architecture and Failing Tests

### Goal

Establish baseline before changing code.

### Steps

1. Pull latest repo.
2. Run type checks.
3. Run backend tests.
4. Run migrations against a fresh DB.
5. Smoke test `/admin/ai-settings`.

### Acceptance Criteria

- Known failures are documented.
- Migration failure, if present, is reproduced.
- Frontend route type failure, if present, is reproduced.

---

## Phase 1: Fix Provider Route Naming and State

### Goal

Make Settings route consistently use `Provider`.

### Files Likely Affected

```text
client/src/components/settings/SettingsDialog.tsx
client/src/stores/settings-dialog-store.ts
client/src/components/settings/panels/AIModelSettingsPanel.tsx
client/src/types/*
```

### Acceptance Criteria

- Settings sidebar shows `Provider`.
- Internal route id is `provider`.
- No stale `ai-models` route type unless intentionally aliased.
- TypeScript passes.

---

## Phase 2: Fix AI Settings Migrations

### Goal

Make backend runtime DB match ORM.

### Files Likely Affected

```text
migrations/alembic/versions/*
app/storage/tables.py
tests/
```

### Acceptance Criteria

- Fresh DB migration creates AI settings tables.
- `/admin/ai-settings` works after migration.
- Tests pass with migrated database.

---

## Phase 3: Secure and Wire Provider Secrets

### Goal

Ensure UI-saved keys can actually be used by LightRAG domain deployment.

### Files Likely Affected

```text
app/api/routes/ai_settings.py
app/api/routes/lightrag_admin.py
app/services/ai_model_settings_service.py
app/services/model_profile_resolver.py
app/storage/repositories/ai_provider_secrets.py
app/services/secret_crypto.py
tests/
```

### Acceptance Criteria

- API keys are encrypted at rest.
- Raw keys are not returned.
- LightRAG domain env generation can resolve DB-stored key.
- Ollama can operate without secret if configured that way.
- Tests cover secret redaction and secret resolution.

---

## Phase 4: Clarify Provider Profile vs Domain Embedding Lock

### Goal

Prevent embedding-model mixing.

### Files Likely Affected

```text
app/lightrag_deploy/models.py
app/lightrag_deploy/service.py
app/services/lightrag_ingestion_service.py
app/services/document_service.py
app/storage/repositories/documents.py
tests/
docs/adr/
```

### Acceptance Criteria

- Domain stores embedding snapshot/fingerprint.
- Document stores domain and embedding fingerprint at ingestion.
- Existing non-empty domain cannot silently switch embedding model.
- Error message explains full reindex requirement if applicable.

---

## Phase 5: Harden Upload → Ingestion Flow

### Goal

Ensure admin upload goes into correct local and LightRAG stores.

### Files Likely Affected

```text
app/api/routes/admin.py
app/services/document_service.py
app/services/lightrag_ingestion_service.py
app/storage/repositories/documents.py
app/workers/tasks.py
tests/
```

### Acceptance Criteria

- Upload requires valid target domain.
- Upload rejects misconfigured domain/provider.
- Document row stores `lightrag_domain_id`.
- Local structure is persisted.
- Remote LightRAG ingest is called for the correct domain.
- Failed ingestion updates job/document status clearly.

---

## Phase 6: Stabilize Retrieval Evidence Contract

### Goal

Make `/retrieve` frontend-ready for context panel.

### Files Likely Affected

```text
app/schemas/retrieval.py
app/retrieval/evidence_mapper.py
app/services/retrieval_asset_resolver.py
client/src/lib/lightrag-client.ts
client/src/components/chat/SidePanel.tsx
tests/
```

### Acceptance Criteria

- Evidence includes stable top-level fields.
- Assets are included or mappable when `include_assets=true`.
- Frontend maps evidence to context panel items.
- Empty/partial evidence is handled gracefully.

---

## Phase 7: Wire Chat → Context Panel + Workspace Tree

### Goal

User chat should populate right panel and workspace tree.

### Files Likely Affected

```text
client/src/lib/lightrag-client.ts
client/src/components/chat/LightRagChatShell.tsx
client/src/components/chat/SidePanel.tsx
client/src/components/chat/WorkspaceTree.tsx
client/src/lib/api/workspace-tree.ts
```

### Acceptance Criteria

- Chat calls `/retrieve`.
- Selected domain is passed.
- Evidence becomes context items.
- Workspace tree loads for selected domain.
- Evidence links to document/page/chunk where possible.

---

## Phase 8: Add Tests and Documentation

### Goal

Protect the complete flow.

### Acceptance Criteria

Tests cover:

- provider admin/user permissions
- secret masking
- provider secret resolution for domain env
- migration schema
- embedding lock
- admin upload
- worker ingestion
- regular user retrieval
- context panel mapping
- workspace tree loading
