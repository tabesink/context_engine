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
