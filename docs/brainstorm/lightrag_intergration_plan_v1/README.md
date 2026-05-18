# Lean LightRAG Integration Docs

This folder documents the implemented external LightRAG integration for `context_engine`.

`context_engine` remains the master multi-user app for auth, users, document mirror records, query routes, CLI access, and API response contracts. LightRAG is an independently deployed HTTP service used for optional retrieval, document ingestion, and graph data.

## Documents

- [integration-plan.md](integration-plan.md): current implementation boundaries and remaining deferrals.
- [http-contract.md](http-contract.md): actual HTTP contract used by `LightRAGRemoteAdapter` and exposed proxy routes.
- [tdd-build-plan.md](tdd-build-plan.md): implemented behavior/test coverage and future test rules.

## Hard Boundary

`context_engine` must not import LightRAG internals from `external/lightrag` or `.references/lightrag`.

All **remote** LightRAG traffic goes through the HTTP adapter and engine:

```text
RetrievalService
  -> app/retrieval/routing_policy.py (local vs remote)
  -> app/retrieval/strategies.py
  -> app/retrieval/lightrag_remote_engine.py (LightRAGRemoteRetrievalEngine)
  -> app/integrations/lightrag_remote_adapter.py (LightRAGRemoteAdapter)
  -> external LightRAG HTTP API
```

`app/integrations/lightrag_adapter.py` defines **`LightRAGAdapter`**: a **local** semantic helper (deterministic hashed embeddings) used when the routing policy selects the local backend. It is not an HTTP client and is unrelated to the remote service.

Graph proxies are registered in `app/api/routes/lightrag.py` and mounted in `app/main.py` with **no router prefix**: `/graphs` and `/graph/label/...` on the Context Engine API.

The TUI talks to those same routes via `cli/services/lightrag.py` (`LightRagService` + `ApiClient`); it never calls LightRAG directly.
