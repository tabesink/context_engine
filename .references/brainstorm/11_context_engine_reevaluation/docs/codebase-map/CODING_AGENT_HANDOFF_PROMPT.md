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
