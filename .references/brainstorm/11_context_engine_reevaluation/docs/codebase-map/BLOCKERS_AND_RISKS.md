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
