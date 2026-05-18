# Junior Developer Start Here

This backend lets authenticated users ask questions over uploaded documents. Admins upload and index documents. Normal users query ready documents through the HTTP API or the interactive `context-engine` terminal UI (thin HTTP client over the same routes).

## The Short Version

The system has one API-facing response contract called `Evidence`.

Evidence can come from:

- Local semantic retrieval over indexed chunks.
- Local navigation retrieval over pages, sections, and document structure.
- Remote LightRAG retrieval when `LIGHTRAG_ENABLED=true`.

LightRAG is optional and external. The default local path still works without a running LightRAG service.

Admins can optionally manage same-machine LightRAG domain containers through Context Engine when `LIGHTRAG_DEPLOY_ENABLED=true`. That deployment control plane writes generated files under `.data/lightrag/`; runtime query/upload/graph traffic still goes through `LightRAGRemoteAdapter`.

## Read Files in This Order

1. `docs/implementation-status.md`
2. `docs/architecture.md`
3. `docs/implementation-plan.md`
4. `app/main.py`
5. `app/core/config.py`
6. `app/domain/models.py`
7. `app/schemas/query.py`
8. `app/api/routes/query.py`
9. `app/services/retrieval_service.py`
10. `app/retrieval/routing_policy.py` and `app/retrieval/strategies.py`
11. `app/retrieval/router.py`
12. `app/retrieval/semantic_engine.py`
13. `app/retrieval/navigation_engine.py`
14. `app/integrations/lightrag_remote_adapter.py`
15. `app/integrations/lightrag_domains.py`
16. `app/lightrag_deploy/service.py`
17. `app/lightrag_deploy/manifest.py`
18. `app/lightrag_deploy/compose.py`
19. `app/api/routes/lightrag.py` and `app/api/routes/lightrag_admin.py`
20. `app/integrations/pageindex_adapter.py`
21. `app/workers/tasks.py`
22. `cli/launcher.py` and `cli/config.py`
23. `cli/api_client.py` and representative modules under `cli/services/`
24. `cli/query_payload.py`
25. `cli/tui/app.py`, `cli/tui/navigation.py`, `cli/tui/screen.py`, `cli/tui/session_flow.py`, and `cli/tui/state.py`
26. `cli/tui/screens/main_menu.py` and `cli/tui/screens/content.py`
27. `cli/main.py` (legacy shim that delegates to the launcher)

## Important Words

- `Document`: uploaded source file and metadata.
- `ParsedDocument`: normalized page/section text extracted from a document.
- `Evidence`: a retrieved piece of text the answer is allowed to use.
- `RetrievalMode`: `semantic`, `navigation`, `hybrid`, or `auto`.
- `RetrievalRoutingPolicy` / strategies: chooses local routing versus `LightRAGRemoteRetrievalEngine` before evidence mapping.
- `Job`: background indexing work run by the worker.
- `context-engine` / `context-tui`: installed launcher commands (same implementation) that open the interactive terminal UI against the REST API.
- `CredentialStore`: local session persistence for bearer tokens (`cli/credentials.py`).
- `LightRAGRemoteAdapter`: HTTP boundary to an external LightRAG service.
- `LightRAGDomainService`: admin control-plane service for generated domain env/manifest/compose files and Docker Compose lifecycle operations.
- `Admin`: user who can mutate documents and indexes.
- `User`: authenticated user who can query ready documents.

## Common Flows

Local admin upload:

```text
admin -> /admin/documents/upload -> file storage -> document row -> indexing job
```

Local indexing:

```text
worker -> parser -> navigation index -> semantic index -> document ready
```

LightRAG upload:

```text
admin -> /admin/documents/upload -> local mirror record -> /documents/upload on LightRAG
```

Query (HTTP shaped):

```text
user -> /query -> RetrievalService -> routing policy + strategies -> local router or remote LightRAG -> evidence -> answer composer
```

Query (terminal UI—it is still the same HTTP contract):

```text
operator -> context-engine TUI -> ApiClient -> /query ...
```

Graph reads:

```text
user -> /graphs or /graph/label/... -> LightRAGRemoteAdapter -> external LightRAG
```

Domain deployment and user listing:

```text
admin -> /admin/lightrag/domains ... -> LightRAGDomainService -> .data/lightrag + Docker Compose runner
user -> GET /lightrag/domains -> safe domain list for query/UI selection (same router module as admin domain APIs)
```

## Rules of Thumb

- Routes should be thin. Put behavior in services.
- Services should not know third-party library details.
- Retrieval engines and adapters should return `Evidence`, never raw external objects.
- Keep LightRAG communication HTTP-only inside `app/integrations/lightrag_remote_adapter.py`.
- Keep LightRAG deployment control inside `app/lightrag_deploy/`; TUI screens and CLI services must not call Docker directly.
- Tests should call public APIs, the launcher/TUI helpers, adapters, or public services (`tests/` uses API tests plus targeted `test_cli_*` modules).
- Do not add a new abstraction unless it hides real complexity.

