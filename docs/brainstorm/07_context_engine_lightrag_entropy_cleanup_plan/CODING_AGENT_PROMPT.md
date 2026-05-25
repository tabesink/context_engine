# Coding Agent Prompt: Remove Local Semantic Fallbacks and Make LightRAG Mandatory

You are working in:

```text
https://github.com/tabesink/context_engine.git
```

Your task is to reduce entropy in the codebase by enforcing one architecture rule:

```text
Remote LightRAG is the only semantic retrieval backend.
Local Context Engine navigation is preserved.
Local semantic retrieval fallback is removed.
```

## Required behavior

Implement these rules:

```text
mode=semantic   → remote LightRAG only
mode=hybrid     → remote LightRAG + local navigation evidence
mode=navigation → local navigation only
mode=auto       → remote LightRAG first
```

If LightRAG is disabled or unavailable for semantic/hybrid/auto retrieval, fail clearly. Do not fall back to local navigation and pretend it is semantic retrieval.

## Files to inspect first

Start with:

```text
app/core/config.py
.env.example
app/services/retrieval_service.py
app/retrieval/routing_policy.py
app/retrieval/router.py
app/retrieval/strategies.py
app/retrieval/navigation_engine.py
app/retrieval/lightrag_remote_engine.py
app/services/document_service.py
app/services/indexing_service.py
app/services/lightrag_ingestion_service.py
app/services/job_service.py
app/workers/tasks.py
app/integrations/lightrag_remote_adapter.py
app/integrations/lightrag_adapter.py
app/indexing/semantic_index_builder.py
app/storage/tables.py
app/storage/repositories/documents.py
app/schemas/query.py
tests/
README.md
docs/
```

## Implementation steps

1. Make LightRAG mandatory in config.
2. Make `LIGHTRAG_ENABLED=false` invalid with a clear error.
3. Remove runtime use of local semantic builder/chunks.
4. Remove or quarantine fake local LightRAG adapter behavior.
5. Clean retrieval routing so semantic mode means remote LightRAG only.
6. Preserve navigation mode and all document navigation APIs.
7. Harden upload/ingestion so semantic indexing cannot bypass LightRAG.
8. Remove silent LightRAG status fallbacks.
9. Remove or deprecate `allow_general_fallback` if it implies unsupported answer synthesis.
10. Update tests and docs.

## Do not do this

Do not:

- add local embeddings
- add a local vector DB
- add another semantic backend
- delete navigation retrieval
- remove pages/sections/assets/thumbnails/source chunks
- implement tenant isolation
- rewrite the entire app
- add LLM answer synthesis

## Acceptance criteria

The implementation is complete when:

- `LIGHTRAG_ENABLED=false` cannot run the app silently.
- `semantic` mode routes only to remote LightRAG.
- `hybrid` mode uses remote LightRAG plus local navigation.
- `navigation` mode remains local and working.
- Runtime code no longer builds or queries local semantic chunks.
- Local navigation is not misnamed as semantic retrieval.
- Tests prove no semantic fallback exists.
- Documentation says LightRAG is required.
