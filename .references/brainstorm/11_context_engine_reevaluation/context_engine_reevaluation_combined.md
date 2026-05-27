# Context Engine Reevaluation Documentation Package

Generated: 2026-05-26



---

# README


# Context Engine Reevaluation Package

Generated: 2026-05-26

This package reevaluates the modified `context_engine` codebase for the Provider settings, LightRAG domain ingestion, user chat retrieval, workspace tree, and context/evidence panel flow.

Repository reviewed:

```text
https://github.com/tabesink/context_engine.git
```

## Intended Reader

This package is written for:

- a coding agent
- a junior developer
- a senior reviewer supervising the implementation
- frontend/backend integration work

## Main Conclusion

The modified codebase has made real progress:

- Settings UI now exposes a **Provider** route.
- Backend now registers an admin `/admin/ai-settings` API.
- Backend has ORM/repository/service concepts for AI model profiles and encrypted provider secrets.
- LightRAG domains now include an embedding snapshot at creation.
- Admin upload, background ingestion, `/retrieve`, workspace-tree backend, and evidence mapping mostly exist.

But the system is **not yet implementation-complete** for the desired product flow.

The top blockers are:

1. Alembic migrations visible in the repo do not create the new AI settings tables or the newer document-domain schema fields.
2. Frontend settings route state still references `ai-models` and does not include `provider`, while the settings dialog uses `provider`.
3. UI-saved provider secrets are not reliably injected into LightRAG domain environment generation.
4. LightRAG domain config is embedding-profile aware, but not fully Provider-profile aware for both LLM and embedding.
5. Chat calls `/retrieve`, but does not yet convert evidence/assets into context-panel items or workspace-tree state.
6. Evidence contract is close, but still needs a stable UI-facing mapping for `page_number`, `section_id`, inline assets, and source-tree links.
7. Upload and ingestion are close, but document/domain/embedding identity should be persisted and enforced consistently.

## Recommended Reading Order

1. `REEVALUATION_SUMMARY.md`
2. `BLOCKERS_AND_RISKS.md`
3. `PROVIDER_SETTINGS_REVIEW.md`
4. `LIGHTRAG_DOMAIN_AND_INGESTION_REVIEW.md`
5. `RETRIEVAL_CONTEXT_WORKSPACE_REVIEW.md`
6. `DATABASE_MIGRATION_REVIEW.md`
7. `IMPLEMENTATION_PLAN.md`
8. `CONCRETE_CODING_TASKS.md`
9. `TEST_PLAN.md`
10. `ADRS_TO_WRITE.md`
11. `CODING_AGENT_HANDOFF_PROMPT.md`



---

# REEVALUATION_SUMMARY


# Context Engine Provider + LightRAG + Evidence Flow Reevaluation

## 1. Executive Summary

The modified codebase is materially closer to the desired workflow:

```text
Admin opens Settings
  → Provider route
  → configures provider/API key/default models
  → creates LightRAG domain with embedding profile
  → uploads document to domain
  → ingestion stores local structure and sends chunks to LightRAG
  → users ask questions through chat
  → /retrieve returns evidence
  → context panel and workspace tree should render evidence
```

However, this flow is not yet complete end to end.

The backend has added the right conceptual pieces for provider settings:

- `/admin/ai-settings`
- `AIModelProfileRow`
- `AIModelSettingsRow`
- `AIProviderSecretRow`
- `AIModelSettingsService`
- encrypted secret repository
- provider kinds: `openai`, `bedrock_openai`, `ollama`

The frontend has also moved in the right direction:

- settings dialog includes a `Provider` route
- `AIModelSettingsPanel` exists
- API client exists for `/admin/ai-settings`
- chat page uses `/retrieve`

But several high-risk integration gaps remain.

## 2. Current Readiness Judgment

| Area | Readiness | Notes |
|---|---:|---|
| Provider UI route | 70% | Visible as Provider, but route store type still appears stale |
| Provider backend API | 75% | Admin routes exist, but test connection is shallow |
| Secret storage | 70% | Encrypted DB secret storage exists, but not fully wired to LightRAG domain env |
| LightRAG domain embedding profile | 75% | Domain create supports embedding snapshot |
| LightRAG domain full provider profile | 45% | LLM still appears global/env-driven, not domain/provider-profile driven |
| Admin upload → local processing | 80% | Good flow exists |
| Admin upload → LightRAG ingestion | 75% | Good flow exists, but embedding/model enforcement needs hardening |
| `/retrieve` backend | 80% | Canonical endpoint exists and is user-accessible |
| Chat → `/retrieve` frontend | 70% | Calls `/retrieve`, but maps evidence into answer text instead of context state |
| Context panel population | 40% | Components exist, but backend evidence is not wired into panel state |
| Workspace tree population | 55% | Backend endpoint exists; frontend has tree component, but chat retrieval does not populate it |
| Migrations/runtime consistency | 25% | Major blocker: visible Alembic chain does not create new AI settings schema |

## 3. Top Blockers

### Blocker 1: Missing AI Settings Migrations

The ORM defines AI settings tables, but visible Alembic migrations do not create them. A fresh deployment may fail when `/admin/ai-settings` tries to query tables that do not exist.

### Blocker 2: Frontend Settings Route Type Mismatch

The settings dialog includes a `provider` route, but the settings route store type still appears to define `ai-models` instead of `provider`. This can break TypeScript builds or route state.

### Blocker 3: UI-Saved Provider Secrets Are Not Fully Used by LightRAG Domain Env Generation

The admin AI settings route can store encrypted provider secrets, but the LightRAG domain admin route constructs the model profile service without a provider secret repository. This means saved DB secrets may not be available when generating domain env.

### Blocker 4: Domain Provider Model Is Embedding-Focused, Not Full Provider-Focused

Domain creation stores an embedding snapshot, but LLM settings still appear to come from global LightRAG deployment settings. The product goal says Provider selection should govern both LLM and embedding defaults.

### Blocker 5: Chat Retrieval Does Not Populate Context Panel / Workspace Tree

The frontend calls `/retrieve`, but the API client currently joins evidence into assistant text and does not call `onContext` with structured evidence or update source tree from the retrieve response.

## 4. Recommended Implementation Direction

Do not rewrite the system.

Implement the missing wiring in this order:

```text
1. Fix migrations/runtime schema.
2. Fix Provider route type/store mismatch.
3. Wire provider secrets into LightRAG domain env generation.
4. Clarify provider profile model: global defaults vs per-domain embedding lock.
5. Persist and enforce document/domain/embedding identity.
6. Convert /retrieve response into frontend context items.
7. Fetch/update workspace tree after upload and/or retrieval.
8. Add tests for all admin/user boundaries and evidence contracts.
```



---

# BLOCKERS_AND_RISKS


# Blockers and Risks

## Critical

### [Critical] ORM and Alembic Migrations Are Out of Sync

**Problem:** The ORM defines AI provider/model settings tables, but the visible Alembic migrations do not create them.

**Evidence to verify in repo:**

- `app/storage/tables.py`
- `migrations/alembic/versions/`
- `0001_baseline.py`
- `0002_document_structure.py`
- `0003_document_pages.py`
- `0004_drop_legacy_navigation.py`
- `0005_document_ingest_job_kind.py`

**Why it matters:** Fresh database deployments may fail at runtime when `/admin/ai-settings` queries tables that do not exist.

**Recommendation:**

Create a new Alembic migration that adds:

```text
ai_model_profiles
ai_model_settings
ai_provider_secrets
```

Also verify whether the existing migrations create:

```text
documents.lightrag_domain_id
```

If not, add it.

**Priority:** P0  
**Effort:** Medium  
**Risk:** Medium

---

### [Critical] Frontend Settings Route Type Appears Inconsistent

**Problem:** `SettingsDialog` uses route id `provider`, but the settings-dialog store still appears to define route union values including `ai-models`, not `provider`.

**Why it matters:** This can break TypeScript checks and settings navigation.

**Recommendation:**

Update the shared settings route type to:

```ts
export type SettingsRoute =
  | "general"
  | "account"
  | "knowledge-graph"
  | "provider";
```

Remove or alias `ai-models` only if backward compatibility is required.

**Priority:** P0  
**Effort:** Low  
**Risk:** Low

---

## High

### [High] DB-Stored Provider Secrets May Not Reach LightRAG Domain Env Generation

**Problem:** Admin AI settings can save encrypted provider secrets, but LightRAG domain service construction may not pass the provider secret repository into the profile service/resolver.

**Why it matters:** An admin can enter an API key in the UI, but domain creation/start may still fail or fall back to environment variables because the saved DB key is not resolved.

**Recommendation:**

Ensure the LightRAG admin dependency constructs:

```python
AIModelSettingsService(
    repository=AIModelSettingsRepository(session),
    secret_repository=AIProviderSecretRepository(session, crypto),
)
```

Then pass that service into `ModelProfileResolver`.

**Priority:** P0/P1  
**Effort:** Low/Medium  
**Risk:** Medium

---

### [High] Provider Settings Are Not Fully Domain-Aware

**Problem:** Domain creation stores an embedding snapshot. LLM settings still appear driven by global LightRAG deployment settings rather than a selected provider/default LLM profile.

**Why it matters:** The UI says "Provider", but domain env generation may still be controlled by root env values. This creates confusing behavior for admins.

**Recommendation:**

Clarify the model:

- Domain must lock embedding profile at creation/first ingestion.
- Domain may either:
  - use global default LLM profile at runtime, or
  - store selected LLM profile explicitly.

For low entropy, use:

```text
Domain stores embedding_profile_snapshot.
Global/default LLM profile can change and applies to new domain env generation.
```

But document this clearly.

**Priority:** P1  
**Effort:** Medium  
**Risk:** Medium

---

### [High] Chat Retrieval Does Not Feed Context Panel and Workspace Tree State

**Problem:** Frontend chat calls `/retrieve`, but structured evidence appears to be joined into message text instead of converted into context panel items and source tree state.

**Why it matters:** Users can ask questions, but the right-side evidence panel and workspace tree will not reliably populate from backend evidence.

**Recommendation:**

In the frontend retrieval client:

- preserve raw `RetrieveResponse`
- map `response.evidence` to `ContextItem[]`
- map `response.assets` into evidence assets
- call `onContext(contextItems, sourceTree)` or equivalent
- fetch `/lightrag/domains/{domain_id}/workspace-tree` after retrieval or upload

**Priority:** P1  
**Effort:** Medium  
**Risk:** Medium

---

### [High] Embedding Model Lock Needs Enforcement

**Problem:** Domain creation stores embedding snapshot/fingerprint, but upload/ingestion should also persist and validate document embedding identity.

**Why it matters:** Mixing embedding models in one vector domain corrupts retrieval assumptions.

**Recommendation:**

At ingestion time:

- resolve domain embedding fingerprint
- store it on document metadata or column
- reject ingestion if requested embedding profile differs from domain snapshot
- block changing domain embedding profile after ingestion unless explicit full reindex flow exists

**Priority:** P1  
**Effort:** Medium  
**Risk:** Medium

---

## Medium

### [Medium] Provider Test Endpoint Is Shallow

**Problem:** The backend provider test method appears to validate secret presence but not perform a real provider request.

**Why it matters:** Admin gets a "passed" result even if base URL/model/token is invalid.

**Recommendation:**

Rename current behavior to "configuration check" or implement real connectivity tests:

- OpenAI-compatible model list call or minimal request
- Ollama base URL health/model list
- Bedrock OpenAI-compatible endpoint test where applicable

**Priority:** P2  
**Effort:** Medium  
**Risk:** Medium

---

### [Medium] Evidence Contract Is Close but Not Yet UI-Stable

**Problem:** Evidence mapper provides many useful fields, but frontend context panel needs a stable contract with page number, source path, document title, chunk/ref id, and assets.

**Recommendation:**

Define a canonical context-panel evidence shape and add mapping tests.

**Priority:** P1/P2  
**Effort:** Medium  
**Risk:** Low

---

### [Medium] Document Domain Column and Metadata Need Alignment

**Problem:** Document metadata contains LightRAG domain info, but the repository may not write the explicit `lightrag_domain_id` column.

**Why it matters:** Future queries, workspace tree, joins, admin filters, and migrations are easier and safer with first-class columns.

**Recommendation:**

Persist both:

```text
documents.lightrag_domain_id
documents.meta.lightrag.domain_id
```

Then gradually prefer the column for filtering.

**Priority:** P2  
**Effort:** Low/Medium  
**Risk:** Medium



---

# PROVIDER_SETTINGS_REVIEW


# Provider Settings Review

## Desired Behavior

Admin should be able to configure Provider settings from the Settings dialog.

Provider settings should include:

```text
provider type
base URL
API key / credential
default LLM model
default embedding model
allowed LLM models
allowed embedding models
connection/configuration status
```

The Settings route should be named:

```text
Provider
```

not:

```text
LLM Model
```

## Current Positive Findings

The modified codebase now includes:

- frontend Settings route labeled `Provider`
- `AIModelSettingsPanel`
- API client for `/admin/ai-settings`
- backend router `/admin/ai-settings`
- backend schemas for AI model profiles and settings
- encrypted provider secret repository
- provider kinds for OpenAI, Bedrock OpenAI-compatible, and Ollama

## Current Gaps

### Gap 1: Route Store Type Needs Update

The UI route registry uses `provider`, but the settings route store may still use `ai-models`.

Required change:

```ts
type SettingsRoute = "general" | "account" | "knowledge-graph" | "provider";
```

### Gap 2: Provider UI Does Not Expose Full Profile Management

The backend API supports creating/updating/testing profiles, but the visible settings panel appears focused on:

- default LLM profile selection
- default embedding profile selection
- provider secret entry

It may not expose:

- create custom profile
- update base URL per profile
- update model name per profile
- test selected profile
- disable profile
- allowed models by provider

Recommendation:

For the next pass, keep UI simple:

```text
Provider Settings
  → Provider secrets
  → Default LLM profile
  → Default embedding profile
  → Test selected/default profile
```

Add profile create/edit later if needed.

### Gap 3: Test Connection Is Not a Real Provider Test

The backend service appears to validate secret presence but not call the provider.

Recommendation:

Either:

```text
Rename to "Validate configuration"
```

or implement actual provider health checks.

## Recommended Backend Provider Model

Use this conceptually:

```text
AIModelProfile
  id
  kind: llm | embedding
  provider: openai | bedrock_openai | ollama
  label
  model
  base_url
  api_key_env_var
  dimensions
  token_limit
  is_active
  created_at
  updated_at
```

Use a separate secret store:

```text
AIProviderSecret
  secret_name
  encrypted_value
  updated_at
```

Frontend responses should expose:

```text
api_key_status: missing | configured | env
```

Never expose raw keys.

## Admin/User Boundary

Provider config endpoints must be admin-only.

Required tests:

- admin can read settings
- regular user cannot read settings
- admin can update defaults
- regular user cannot update defaults
- admin can set secret
- secret response is masked
- raw key never appears in JSON response



---

# LIGHTRAG_DOMAIN_AND_INGESTION_REVIEW


# LightRAG Domain and Ingestion Review

## Desired Flow

```text
Admin selects Provider/default embedding profile
  → creates LightRAG domain
  → domain stores embedding snapshot
  → admin uploads document to domain
  → worker parses document
  → local pages/sections/chunks/assets are stored
  → chunks are ingested into selected LightRAG domain
  → domain and document become available for retrieval
```

## Current Positive Findings

The modified codebase appears to include:

- LightRAG admin routes
- LightRAG domain create request with `embedding_profile_id`
- domain embedding snapshot
- provider/model resolver
- domain env generation
- admin upload route with optional domain parameter
- domain validation before upload
- background ingestion job
- parsed local structure persistence
- remote LightRAG chunk ingestion

## Important Architecture Issue

The domain model is currently stronger for **embedding profile snapshots** than for full Provider profile control.

That may be acceptable if documented:

```text
Embedding profile is domain-level and locked.
LLM profile is global/default and may change over time.
```

But the Settings UI says Provider, so the product behavior must be explicit.

## Recommended Domain Rules

### Rule 1: Domain Must Lock Embedding Profile

A domain should store:

```text
embedding_profile_id
embedding_provider
embedding_binding
embedding_base_url
embedding_model
embedding_dimensions
embedding_token_limit
embedding_fingerprint
embedding_locked_at
```

### Rule 2: Existing Domains Cannot Silently Switch Embedding Model

Allowed options:

```text
Option A: never allow embedding model change after domain creation.
Option B: allow change only before first document ingestion.
Option C: allow change only through explicit full reindex workflow.
```

Recommended low-entropy choice:

```text
Option B now.
Option C later.
```

### Rule 3: Upload Must Persist Domain and Embedding Identity

Document should store:

```text
lightrag_domain_id
embedding_profile_id or embedding_fingerprint
ingestion_status
```

Store it both as first-class DB fields and in metadata if needed for backward compatibility.

## Current Risk: Secret Resolution During Domain Env Generation

The domain env generation path must be able to resolve secrets saved through the admin Provider settings UI.

If the domain service only sees OS environment variables, then UI-saved API keys will not work.

Required fix:

```text
LightRAGDomainService
  → ModelProfileResolver
  → AIModelSettingsService
  → AIProviderSecretRepository
  → SecretCryptoService
```

## Upload/Ingestion Acceptance Criteria

- Admin upload requires valid target domain.
- Upload fails clearly if domain does not exist.
- Upload fails clearly if domain is not ready/configured.
- Upload persists document with domain ID.
- Worker stores local parsed structure.
- Worker sends chunks to correct LightRAG domain.
- Worker updates job status on success/failure.
- Ingestion records embedding fingerprint used.
- Mismatched embedding profile is rejected.



---

# RETRIEVAL_CONTEXT_WORKSPACE_REVIEW


# Retrieval, Context Panel, and Workspace Tree Review

## Desired Flow

```text
Authenticated user types a question
  → frontend sends request to /retrieve
  → request includes selected LightRAG domain
  → backend validates user and domain
  → LightRAG semantic retrieval runs
  → local metadata enrichment runs
  → backend returns stable evidence response
  → frontend maps evidence to context panel items
  → frontend updates or fetches workspace tree
```

## Current Positive Findings

The modified codebase appears to include:

- `/retrieve` route
- user-accessible retrieval, not admin-only
- retrieval service
- LightRAG remote retrieval engine
- local navigation retrieval engine
- evidence mapper
- optional asset resolver
- workspace-tree backend route
- workspace-tree service
- chat frontend using `/retrieve`
- right-side panel and workspace tree components

## Main Gap

The frontend retrieval client appears to convert evidence into assistant message text, but does not yet route structured evidence into:

- `contextItems`
- `sourceTree`
- side panel asset cards
- workspace tree updates

## Recommended Frontend Mapping

After `/retrieve` returns:

```ts
const response = await retrieve(...);

const contextItems = response.evidence.map((e, index) => ({
  id: e.reference_id ?? e.evidence_id ?? `E${index + 1}`,
  title: e.document_title ?? e.source_path ?? "Source",
  excerpt: e.text,
  sourcePath: e.source_path,
  documentId: e.document_id,
  chunkId: e.chunk_id,
  pageNumber: e.page_number ?? e.page_start,
  score: e.score,
  assets: assetsForEvidence(e, response.assets),
}));
```

Then call:

```ts
onContext(contextItems, sourceTree);
```

or update the relevant chat state/store.

## Recommended Backend Evidence Contract

Stable top-level evidence fields:

```text
reference_id
document_id
document_title
source_path
chunk_id
section_id
section_title
page_number
page_start
page_end
score
text
metadata
assets
```

It is acceptable to keep assets as a separate response-level array, but frontend mapping must be documented and tested.

## Workspace Tree Strategy

Simplest approach:

1. On chat domain selection:
   - fetch `/lightrag/domains/{domain_id}/workspace-tree`
2. After upload/reingestion success:
   - refetch tree
3. After retrieval:
   - optionally highlight evidence-linked nodes

Tree shape:

```text
Workspace
  → Domain
      → Document
          → Section
              → Page
              → Chunk
              → Asset
```

## Required Tests

Backend:

- regular user can call `/retrieve`
- regular user can call workspace-tree endpoint
- `/retrieve` returns evidence with document/source/chunk fields
- include_assets returns assets when available
- retrieval fails clearly if domain unavailable

Frontend:

- chat calls `/retrieve`
- selected domain is passed
- evidence becomes context panel items
- empty evidence renders gracefully
- workspace tree loads for selected domain
- evidence source can link or highlight tree/document node



---

# DATABASE_MIGRATION_REVIEW


# Database and Migration Review

## Main Finding

The ORM appears ahead of the visible migration chain.

The code defines new AI settings and secret storage tables, but the visible migrations do not appear to create them.

## Tables/Columns to Verify

### AI Settings Tables

Required if backend uses ORM rows:

```text
ai_model_profiles
ai_model_settings
ai_provider_secrets
```

### Document Domain Fields

Verify migrations create:

```text
documents.lightrag_domain_id
```

Also verify the repository writes it during document creation.

### Optional Future Fields

Recommended for stronger provider/domain consistency:

```text
documents.embedding_profile_id
documents.embedding_fingerprint
documents.ingestion_status
lightrag_domains.provider_profile_id
lightrag_domains.embedding_profile_id
lightrag_domains.embedding_fingerprint
lightrag_domains.embedding_locked_at
```

If domains remain manifest-backed, these fields may live in the manifest instead of DB. But the source of truth must be explicit.

## Required Migration Plan

### Migration N: AI Settings Tables

Create:

```text
ai_model_profiles
ai_model_settings
ai_provider_secrets
```

Add uniqueness constraints:

```text
ai_model_profiles.id unique
ai_provider_secrets.secret_name unique
```

### Migration N+1: Document Domain Column

If missing:

```text
ALTER TABLE documents ADD COLUMN lightrag_domain_id TEXT NULL;
CREATE INDEX ix_documents_lightrag_domain_id ON documents(lightrag_domain_id);
```

Backfill from JSON metadata if possible.

### Migration N+2: Optional Embedding Fingerprint Fields

If needed:

```text
documents.embedding_fingerprint TEXT NULL
documents.embedding_profile_id TEXT NULL
```

## Migration Acceptance Criteria

- Fresh database can run all migrations.
- Existing database can migrate without data loss.
- `/admin/ai-settings` works after migration.
- Admin upload writes domain ID.
- Workspace tree can query ready documents by domain.
- Tests cover migration-created schema expectations.

## Runtime Smoke Tests

Run:

```bash
alembic upgrade head
pytest tests/test_ai_settings*.py
pytest tests/test_lightrag*.py
pytest tests/test_retrieve*.py
pytest tests/test_workspace_tree*.py
```

Then manually verify:

```text
GET /admin/ai-settings as admin
PUT /admin/ai-settings/provider-secrets/OPENAI_API_KEY
POST /admin/lightrag/domains
POST /admin/documents/upload
POST /retrieve
GET /lightrag/domains/{domain_id}/workspace-tree
```



---

# IMPLEMENTATION_PLAN


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



---

# CONCRETE_CODING_TASKS


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



---

# TEST_PLAN


# Test Plan

## Backend Tests

### AI Settings

- admin can get AI settings
- regular user cannot get AI settings
- admin can update default LLM profile
- admin can update default embedding profile
- regular user cannot update defaults
- admin can create profile
- admin can update profile
- admin can set provider secret
- secret response is masked
- raw secret is not returned
- raw secret is not logged
- Ollama profile does not require API key if configured as local

### Migrations

- fresh DB migration creates AI settings tables
- fresh DB migration creates or preserves document domain fields
- `/admin/ai-settings` works after migration
- rollback/downgrade posture documented

### LightRAG Domains

- admin can create domain with embedding profile
- domain stores embedding snapshot/fingerprint
- domain env generation uses embedding snapshot
- domain env generation can use DB-stored provider secret
- missing provider secret fails clearly
- regular user cannot create/start/stop/delete domain
- domain cannot silently change embedding model after ingestion

### Upload and Ingestion

- regular user cannot upload
- admin upload requires valid domain
- upload fails for unknown domain
- upload persists `lightrag_domain_id`
- upload creates job
- worker persists local structure
- worker sends chunks to correct LightRAG domain
- failed LightRAG ingest marks job failed
- retry/requeue behavior works where expected
- document stores embedding fingerprint used

### Retrieval

- unauthenticated user cannot retrieve
- authenticated regular user can retrieve
- retrieval uses selected domain
- invalid domain fails clearly
- document filter outside domain fails clearly
- evidence includes stable fields
- `include_assets=true` returns assets where available
- LightRAG unavailable returns clear error

### Workspace Tree

- regular user can fetch workspace tree
- tree is domain-scoped
- tree excludes non-ready/unauthorized docs as intended
- tree includes documents, sections, pages, chunks, assets
- tree handles empty domain gracefully

## Frontend Tests

### Settings

- Settings sidebar shows Provider
- Provider route is admin-only
- non-admin does not see Provider route
- API key input masks stored status
- raw key is not displayed after save
- default LLM/embedding selection loads from backend
- save/update states display errors clearly

### Chat Retrieval

- chat sends `/retrieve`
- selected domain is included
- evidence response populates context panel
- no evidence shows empty state
- backend error shows user-friendly message

### Workspace Tree

- tree fetches selected domain structure
- tree updates on domain change
- tree renders documents and sections
- evidence click can link/highlight matching source where implemented

## Manual Smoke Test Script

1. Start fresh DB.
2. Run migrations.
3. Start API and frontend.
4. Login as admin.
5. Open Settings → Provider.
6. Set provider secret.
7. Select default LLM and embedding.
8. Create LightRAG domain with embedding profile.
9. Upload document to domain.
10. Confirm job succeeds.
11. Login as regular user.
12. Select domain in chat retrieval settings.
13. Ask a question.
14. Confirm answer/evidence returns.
15. Confirm context panel shows evidence.
16. Confirm workspace tree shows domain documents.



---

# ADRS_TO_WRITE


# ADRs to Write

## ADR-001: Provider Profile Model

Decision:

- How providers, base URLs, model names, and API key references are represented.
- Whether provider profiles are global, per-domain, or both.

Recommended:

```text
Global AIModelProfile rows.
Domain stores embedding profile snapshot.
Default LLM profile remains global unless product requires per-domain LLM.
```

## ADR-002: API Key and Secret Handling

Decision:

- Whether secrets are env-only, DB-encrypted, or both.
- How UI-saved secrets are used by domain deployment.
- What masking/redaction is required.

Recommended:

```text
Support encrypted DB secrets for local trusted deployments.
Never return raw keys.
Allow env-managed secrets as fallback.
```

## ADR-003: LightRAG Domain Embedding Lock

Decision:

- Whether embedding profile can change after domain creation or ingestion.

Recommended:

```text
Domain embedding can be changed only while domain is empty.
After first successful ingestion, full reindex is required.
```

## ADR-004: Provider vs LLM vs Embedding UI Semantics

Decision:

- How Settings → Provider explains LLM and embedding defaults.

Recommended:

```text
Provider route manages credentials and model profiles.
Embedding model is domain-critical.
LLM model is runtime/default behavior and may be changed more freely.
```

## ADR-005: Canonical Retrieval API

Decision:

- Whether `/retrieve` is the only chat/evidence retrieval endpoint.

Recommended:

```text
Use /retrieve as canonical.
Do not introduce duplicate query endpoints.
```

## ADR-006: Evidence and Context Panel Contract

Decision:

- Stable fields backend must return for context panel and workspace tree linking.

Recommended contract:

```text
reference_id
document_id
document_title
source_path
chunk_id
section_id
section_title
page_number
page_start
page_end
score
text
assets
metadata
```

## ADR-007: Workspace Tree Source of Truth

Decision:

- Whether workspace tree is populated from retrieval evidence or dedicated endpoint.

Recommended:

```text
Use dedicated workspace-tree endpoint for tree.
Use retrieval evidence to highlight/select nodes.
```

## ADR-008: Shared Corpus Read Model

Decision:

- Whether all authenticated users can read all ready documents in visible domains.

Recommended:

```text
V1 shared corpus.
Admin-only writes.
Regular users can retrieve and view workspace tree.
```



---

# CODING_AGENT_HANDOFF_PROMPT


# Coding Agent Handoff Prompt

You are a coding agent working on `context_engine`.

Your goal is to complete the Provider → LightRAG Domain → Upload/Ingestion → Retrieve → Context Panel/Workspace Tree flow.

Do not rewrite the system.

Work incrementally.

## Product Flow to Make True

```text
Admin opens Settings → Provider
  → configures provider/API key/default models
  → creates LightRAG domain with embedding profile
  → uploads document to that domain
  → backend stores local document structure and ingests chunks into LightRAG
  → regular user selects domain and asks question in chat
  → /retrieve returns stable evidence
  → frontend context panel and workspace tree show sources
```

## Start by Verifying These Blockers

1. Run migrations on a fresh DB.
2. Confirm AI settings tables exist.
3. Confirm Settings route type includes `provider`.
4. Confirm `/admin/ai-settings` works after migration.
5. Confirm UI-saved provider secret reaches LightRAG domain env generation.
6. Confirm upload persists document domain ID.
7. Confirm `/retrieve` evidence reaches context panel.

## Fix Order

```text
Phase 1: migrations
Phase 2: Provider route type mismatch
Phase 3: provider secret resolution into domain env
Phase 4: domain embedding lock and document embedding identity
Phase 5: upload/ingestion hardening
Phase 6: /retrieve evidence contract
Phase 7: frontend context panel mapping
Phase 8: workspace tree fetch/update
Phase 9: tests and docs
```

## Non-Negotiable Rules

- Provider settings are admin-only.
- API keys are never returned unmasked.
- Regular users can retrieve and view workspace tree.
- Regular users cannot upload/manage domains/configure providers.
- A LightRAG domain cannot silently mix embedding models.
- `/retrieve` remains canonical chat/evidence endpoint.
- Frontend should not parse raw LightRAG internals for core evidence display.
- Add tests for each changed behavior.

## First Files to Inspect

```text
app/main.py
app/api/routes/ai_settings.py
app/schemas/ai_settings.py
app/services/ai_model_settings_service.py
app/storage/tables.py
app/storage/repositories/ai_model_settings.py
app/storage/repositories/ai_provider_secrets.py
app/services/secret_crypto.py
app/domain/ai_models.py
app/api/routes/lightrag_admin.py
app/lightrag_deploy/models.py
app/lightrag_deploy/service.py
app/lightrag_deploy/compose.py
app/services/model_profile_resolver.py
app/api/routes/admin.py
app/services/document_service.py
app/services/lightrag_ingestion_service.py
app/api/routes/retrieve.py
app/services/retrieval_service.py
app/retrieval/evidence_mapper.py
app/api/routes/workspace_tree.py
app/services/workspace_tree_service.py
client/src/components/settings/SettingsDialog.tsx
client/src/stores/settings-dialog-store.ts
client/src/components/settings/panels/AIModelSettingsPanel.tsx
client/src/lib/api/ai-settings.ts
client/src/lib/lightrag-client.ts
client/src/components/chat/LightRagChatShell.tsx
client/src/components/chat/SidePanel.tsx
client/src/components/chat/WorkspaceTree.tsx
```

## Definition of Done

- Fresh DB migrates successfully.
- Admin can configure Provider.
- Provider secret stored securely and not leaked.
- LightRAG domain can use selected embedding profile and provider secret.
- Upload into domain succeeds.
- Ingestion sends chunks to correct LightRAG domain.
- Regular user can retrieve.
- Evidence appears in context panel.
- Workspace tree loads selected domain contents.
- Tests cover admin/user boundaries, migrations, provider config, ingestion, retrieval, and frontend mapping.
