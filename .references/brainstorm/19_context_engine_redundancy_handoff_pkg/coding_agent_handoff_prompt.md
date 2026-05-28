# Coding Agent Handoff Prompt — Context Engine Redundancy Reduction

You are working in `https://github.com/tabesink/context_engine.git`.

Read `context_engine_redundancy_implementation_plan.md` first. Your goal is to implement the plan in small safe PRs. Do not perform broad rewrites. Do not remove destructive routes without tests, compatibility notes, and explicit deprecation strategy.

## Start Here

Run these commands and save outputs:

```bash
python -m pytest -q
cd client && npm run lint && npm run build
rg -n "recreate|repair|regenerate|purge|remove\(|permanent|up_domain|down_domain" app tests client scripts docs
rg -n "LightRAGDomainService|DomainPurgeService|LightRAGDomainLifecycleService|LightRAGDomainRegistry" app tests
rg -n "status-poller|refresh_pending_lightrag_statuses|ingestion-status|track_id|pipeline_status|status_counts" app tests client
rg -n "apiRequest|resolveApiBase|fetch\(|/lightrag/domains|/admin/lightrag/domains" client/src
rg -n "ContextStream|SourceNavigator|WorkspaceTree|AssetCards|sourceContext|contextByAssistantId" client/src
rg -n "deprecated|legacy|context-tui|context-engine|cli" .
```

## Non-Negotiables

- Preserve current behavior unless a task explicitly calls for deprecation.
- Keep frontend from calling LightRAG directly.
- Keep Context Engine as the single API/auth boundary.
- Do not collapse archive and purge.
- Do not expose permanent deletion without preview/confirm.
- Do not make workspace tree clicks trigger retrieval.
- Do not mutate retrieval filters on source selection.
- Do not add dependencies.

## PR Order

1. Baseline + lifecycle semantics docs.
2. Hide/relabel redundant admin UI lifecycle actions.
3. Consolidate `LightRAGDomainService` private helpers.
4. Deprecate/gate permanent delete query path in favor of purge.
5. Extract shared LightRAG failure normalizer.
6. Normalize frontend API client and domain/asset types.
7. Verify source-context route/client completion.
8. Isolate CLI/TUI expectations.

## Final Output Required

For each PR, provide:

- changed files
- behavior changes, if any
- compatibility notes
- tests run
- before/after redundancy removed
- deferred follow-ups
