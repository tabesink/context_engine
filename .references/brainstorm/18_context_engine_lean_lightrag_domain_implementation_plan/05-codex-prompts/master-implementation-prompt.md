# Master Implementation Prompt

```text
You are a senior software architect and coding agent working in the Context Engine repo.

Goal: simplify LightRAG Docker domain deployment to a low-entropy model.

Final lifecycle actions:
- Create
- Start
- Stop
- Delete

Remove public/product/API actions:
- repair
- recreate
- regenerate
- purge-preview
- purge

Remove retrieval defaults from the domain create UI/API/runtime editing surface:
- top_k
- chunk_top_k
- chunk_rerank_top_k
- token budgets
- retrieval presets

Retrieval defaults must come from backend/deployment settings and be written into domain.env during runtime artifact generation.

Important design decisions:
1. Create configures the domain only. It must not auto-start or call repair.
2. Start is the only boot/recovery path. It internally prepares artifacts, writes domain.env, writes Compose, provisions Postgres, starts Docker, probes health, and persists status.
3. Delete is safe remove/archive. It must not hard-delete documents, uploads, chunks, assets, jobs, or parsed structure.
4. Provider keys/model profiles remain editable through AI Settings. Running domains need restart to apply changed env values.
5. Embedding model is selected at domain creation and treated as domain identity after ingestion.

Implementation phases:
- Phase 0: impact scan.
- Phase 1: frontend UI simplification.
- Phase 2: API route/schema cleanup.
- Phase 3: service consolidation.
- Phase 4: retrieval defaults moved to backend config/domain.env.
- Phase 5: optional runtime config resolver.
- Phase 6: tests/docs cleanup.

Before coding:
- Search call sites for repair/recreate/regenerate/purge/purgePreview/retrieval defaults/start true.
- Report impact.
- Do not delete useful internal logic; move it behind Start/private helpers.

Return a concise implementation plan first, then implement in small reviewable patches.
```
