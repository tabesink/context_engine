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
