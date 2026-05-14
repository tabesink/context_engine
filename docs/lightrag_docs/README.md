# Lean LightRAG Integration Docs

This folder documents the implemented external LightRAG integration for `context_engine`.

`context_engine` remains the master multi-user app for auth, users, document mirror records, query routes, CLI access, and API response contracts. LightRAG is an independently deployed HTTP service used for optional retrieval, document ingestion, and graph data.

## Documents

- [integration-plan.md](integration-plan.md): current implementation boundaries and remaining deferrals.
- [http-contract.md](http-contract.md): actual HTTP contract used by `LightRAGRemoteAdapter` and exposed proxy routes.
- [tdd-build-plan.md](tdd-build-plan.md): implemented behavior/test coverage and future test rules.

## Hard Boundary

`context_engine` must not import LightRAG internals from `external/lightrag` or `.references/lightrag`.

All LightRAG communication goes through one adapter boundary:

```text
context_engine app
  -> app/integrations/lightrag_remote_adapter.py
  -> external LightRAG HTTP API
```

Current app-facing graph routes are mounted directly on the backend as `/graphs` and `/graph/label/...`; there is no `/lightrag` API prefix.
