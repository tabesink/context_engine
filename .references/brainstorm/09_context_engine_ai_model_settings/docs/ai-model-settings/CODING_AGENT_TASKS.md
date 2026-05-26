# Coding Agent Implementation Tasks

## Phase 0: Safety and Design Alignment

### Task 0.1 — Add ADR

Create:

```text
docs/adr/ADR-ai-model-settings-and-domain-embedding-lock.md
```

Acceptance criteria:

- explains embedding immutability
- explains LLM mutability
- explains admin-only control
- explains why raw secrets stay out of browser

## Phase 1: Backend Schema

### Task 1.1 — Add AI model domain models

Files:

```text
app/domain/ai_models.py
app/schemas/ai_settings.py
```

Acceptance criteria:

- provider enums exist
- request/response schemas exist
- response schemas redact secrets

### Task 1.2 — Add DB migration

Files:

```text
migrations/versions/<timestamp>_add_ai_model_settings.py
app/storage/tables.py
```

Acceptance criteria:

- `ai_model_profiles` table exists
- `ai_model_settings` table exists
- migration upgrades and downgrades cleanly
- tests use new schema without failing

## Phase 2: Backend Services and API

### Task 2.1 — Add repository

Files:

```text
app/storage/repositories/ai_model_settings.py
```

Acceptance criteria:

- CRUD profiles
- get/set defaults
- list enabled profiles
- no raw secret values stored

### Task 2.2 — Add service

Files:

```text
app/services/ai_model_settings_service.py
app/services/model_profile_resolver.py
```

Acceptance criteria:

- can seed default profiles
- validates profile kind/provider
- checks secret env var status
- resolves LightRAG env config
- computes embedding fingerprint

### Task 2.3 — Add admin route

Files:

```text
app/api/routes/ai_settings.py
app/main.py
```

Acceptance criteria:

- `/admin/ai-settings` routes registered
- all routes require admin
- regular user receives 403/401
- secrets redacted

## Phase 3: LightRAG Domain Integration

### Task 3.1 — Extend domain models

Files:

```text
app/lightrag_deploy/models.py
```

Acceptance criteria:

- create request accepts `embedding_profile_id`
- domain manifest includes embedding snapshot
- existing domain manifests still load

### Task 3.2 — Wire profile resolution into domain creation

Files:

```text
app/api/routes/lightrag_admin.py
app/lightrag_deploy/service.py
```

Acceptance criteria:

- domain creation uses requested/default embedding profile
- embedding snapshot persisted
- LLM profile persisted or inherited
- audit log records profile IDs

### Task 3.3 — Render domain.env from profile snapshots

Files:

```text
app/lightrag_deploy/compose.py
```

Acceptance criteria:

- generated domain.env includes LLM settings
- generated domain.env includes embedding settings
- existing storage settings are preserved
- no profile change mutates existing domain embedding snapshot

## Phase 4: Frontend Settings Shell

### Task 4.1 — Add settings layout

Files:

```text
client/src/app/settings/layout.tsx
```

Acceptance criteria:

- left rail with Account, Knowledge Graphs, AI Models
- AI Models visible only to admins
- layout matches existing app style

### Task 4.2 — Add AI Models page

Files:

```text
client/src/app/settings/models/page.tsx
client/src/api/ai-settings.ts
client/src/types/ai-settings.ts
```

Acceptance criteria:

- admin can view defaults
- admin can set default LLM
- admin can set default embedding
- status badges show key/missing/offline state
- helper text explains embedding lock

## Phase 5: Domain Creation UI

### Task 5.1 — Add embedding dropdown

Files depend on current domain creation UI location.

Acceptance criteria:

- dropdown populated from enabled embedding profiles
- default selected
- helper text says locked after creation
- request sends `embedding_profile_id`

### Task 5.2 — Show domain model summary

Acceptance criteria:

- domain cards/table show embedding model and dims
- legacy domains show warning
- LLM default/override shown

## Phase 6: Tests

### Backend tests

Add:

```text
tests/test_ai_settings_api.py
tests/test_ai_model_settings_service.py
tests/test_lightrag_domain_model_lock.py
```

Required tests:

- non-admin cannot access settings
- default profiles can be changed by admin
- profile with missing secret cannot be set active unless allowed
- new domain snapshots embedding profile
- existing domain snapshot does not change when default changes
- generated domain.env includes expected values

### Frontend tests

If frontend test framework exists:

- admin sees AI Models nav
- non-admin does not
- embedding dropdown helper text appears
- save/default flow handles API errors

## Phase 7: Documentation

Update:

```text
README.md
.env.example
.env.lightrag-provider.example
docs/ai-model-settings/
```

Acceptance criteria:

- provider profile setup documented
- OpenAI, Bedrock OpenAI-compatible, and Ollama examples included
- warning against mixing embeddings included
- secret handling documented

## Rollback Plan

If issues appear:

1. keep old `.env.lightrag-provider.example` behavior
2. disable `/admin/ai-settings` route from `app/main.py`
3. domain creation falls back to existing env-driven config
4. no migration rollback unless tables break startup

Do not roll back domain manifests without backing up `.data/lightrag/domains.json`.
