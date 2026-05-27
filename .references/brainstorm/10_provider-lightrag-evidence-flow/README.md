# Context Engine Provider + LightRAG Ingestion + Evidence Flow Review Package

Generated: 2026-05-26

Repository reviewed:

```text
https://github.com/tabesink/context_engine.git
```

## Purpose

This package is intended to be handed to a coding agent or junior developer before implementation.

It reviews whether the modified `context_engine` codebase is ready for this target flow:

```text
Admin configures Provider in Settings
  → admin creates/selects LightRAG domain
  → admin uploads documents to that domain
  → documents ingest into local Context Engine storage and LightRAG domain storage
  → regular users ask questions from chat input
  → Context Engine returns evidence
  → workspace tree and context panel render that evidence
```

## Main Conclusion

The repo has several strong building blocks already:

- backend `/retrieve` route exists and is authenticated-user accessible
- admin upload route exists and requires admin
- LightRAG domain lifecycle APIs exist
- LightRAG generated domain env files already receive LLM/embedding provider environment variables
- local document structure, source chunks, and assets are persisted
- workspace tree endpoint exists and is user-accessible
- frontend has chat, retrieval settings, workspace tree, and context-panel components

But the desired provider-centered workflow is **not implementation-ready yet**.

The major missing links are:

1. no backend provider/settings router is registered
2. no DB-backed provider profile model was found in the inspected schema
3. LightRAG domain records do not store provider profile ID or embedding-model lock metadata
4. frontend Settings still has an `ai-models` route concept instead of a `provider` route
5. frontend chat appears wired to a streaming LightRAG-style contract rather than the backend `/retrieve` evidence contract
6. context panel/frontend evidence types do not yet match backend `RetrieveResponse` / `EvidenceResponse`
7. workspace tree UI is not clearly wired to backend `/lightrag/domains/{domain_id}/workspace-tree`

## Recommended Reading Order

1. `EXECUTIVE_SUMMARY.md`
2. `CURRENT_ARCHITECTURE_MAP.md`
3. `PROVIDER_SETTINGS_REVIEW.md`
4. `LIGHTRAG_DOMAIN_AND_INGESTION_REVIEW.md`
5. `RETRIEVAL_CHAT_EVIDENCE_REVIEW.md`
6. `WORKSPACE_TREE_CONTEXT_PANEL_CONTRACT.md`
7. `IMPLEMENTATION_PLAN.md`
8. `CONCRETE_CODING_TASKS.md`
9. `TEST_PLAN.md`
10. `ADRS_TO_WRITE.md`
11. `CODING_AGENT_PROMPT.md`

## Important Caveat

This review was performed by web-based repository inspection. The repository could not be cloned or tested locally from the execution environment because network DNS resolution for `github.com` failed. Treat all findings as code-inspection findings and run the test suite locally before implementation.
