# Junior Developer Start Here

This backend lets authenticated users ask questions over uploaded documents. Admins upload and ingest documents. Normal users query ready documents through the HTTP API or the interactive `context-engine` terminal UI (thin HTTP client over the same routes).

## The Short Version

The system has one API-facing response contract called `Evidence`.

Evidence can come from:

- Local navigation retrieval over pages, sections, and document structure.
- Remote LightRAG semantic retrieval.

LightRAG is external and is the only semantic retrieval engine. Local navigation/page browsing remains separate local capability.
The public retrieval API is evidence-only through `POST /retrieve`.

Admins can optionally manage same-machine LightRAG domain containers through Context Engine when `LIGHTRAG_DEPLOY_ENABLED=true`. That deployment control plane writes generated files under `.data/lightrag/`; runtime retrieve/upload/graph traffic still goes through `LightRAGRemoteAdapter`.

For model providers in managed domains:

- Keep LightRAG bindings as `openai` unless you are explicitly changing bindings end-to-end.
- Bedrock OpenAI-compatible mode is configured with `LIGHTRAG_LLM_BINDING=openai` and `LIGHTRAG_LLM_BINDING_HOST=https://bedrock-runtime.<region>.amazonaws.com/openai/v1`.
- Do not confuse per-domain registry `api_key` values (Context Engine -> LightRAG auth) with `LIGHTRAG_LLM_BINDING_API_KEY` (LightRAG -> model provider auth).

## Read Files in This Order

1. `docs/implementation-status.md`
2. `docs/architecture.md`
3. `docs/implementation-plan.md`
4. `app/main.py`
5. `app/core/config.py`
6. `app/domain/models.py`
7. `app/schemas/retrieval.py`
8. `app/api/routes/retrieve.py`
9. `app/services/retrieval_service.py`
10. `app/retrieval/routing_policy.py` and `app/retrieval/strategies.py`
11. `app/retrieval/rich_navigation_engine.py`
12. `app/retrieval/lightrag_remote_engine.py`
13. `app/retrieval/hybrid_merger.py`
14. `app/integrations/lightrag_remote_adapter.py`
15. `app/integrations/lightrag_domains.py`
16. `app/lightrag_deploy/service.py`
17. `app/lightrag_deploy/manifest.py`
18. `app/lightrag_deploy/compose.py`
19. `app/api/routes/lightrag.py` and `app/api/routes/lightrag_admin.py`
20. `app/storage/repositories/document_processing.py`
21. `app/workers/tasks.py`
22. `cli/launcher.py` and `cli/config.py`
23. `cli/api_client.py` and representative modules under `cli/services/`
24. `cli/retrieve_payload.py`
25. `cli/tui/app.py`, `cli/tui/navigation.py`, `cli/tui/screen.py`, `cli/tui/session_flow.py`, and `cli/tui/state.py`
26. `cli/tui/screens/main_menu.py` and `cli/tui/screens/content.py`
27. `cli/main.py` (legacy shim that delegates to the launcher)

## Important Words

- `Document`: uploaded source file and metadata.
- `DocumentStructure`: canonical Control Plane structure for pages, sections, blocks, source chunks, and assets.
- `SourceChunk`: a citation/navigation unit that links text to pages, sections, blocks, and assets. It is not a semantic chunk and does not contain embeddings.
- `Evidence`: a retrieved piece of text the answer is allowed to use.
- `RetrievalMode`: `semantic`, `navigation`, `hybrid`, or `auto`.
- `RetrievalRoutingPolicy` / strategies: chooses local routing (`RichNavigationEngine`) versus `LightRAGRemoteRetrievalEngine` before evidence mapping.
- `Job`: background indexing work run by the worker.
- `context-engine`: installed launcher command that opens the interactive terminal UI against the REST API.
- `CredentialStore`: local session persistence for bearer tokens (`cli/credentials.py`).
- `LightRAGRemoteAdapter`: HTTP boundary to an external LightRAG service.
- `LightRAGDomainService`: admin control-plane service for generated domain env/manifest/compose files and Docker Compose lifecycle operations.
- `LLM_BINDING*` / `EMBEDDING_BINDING*`: generated LightRAG runtime provider keys written to per-domain `domain.env` files.
- `Admin`: user who can mutate documents and ingestion jobs.
- `User`: authenticated user who can query ready documents.

## Common Flows

Admin upload:

```text
admin -> /admin/documents/upload -> local mirror record -> document_ingest job
```

Retrieve (HTTP shaped):

```text
user -> /retrieve -> RetrievalService -> routing policy + strategies -> local rich navigation or remote LightRAG -> evidence
```

Retrieve (terminal UI—it is still the same HTTP contract):

```text
operator -> context-engine TUI -> ApiClient -> /retrieve
```

Graph reads:

```text
user -> /lightrag/domains/{domain_id}/graphs or /lightrag/domains/{domain_id}/graph/labels... -> LightRAGRemoteAdapter -> external LightRAG
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
- Keep local deterministic navigation in `DocumentStructure` + `RichNavigationEngine`; do not reintroduce legacy `parsed_documents`/`navigation_indexes` runtime paths.
- Keep LightRAG deployment control inside `app/lightrag_deploy/`; TUI screens and CLI services must not call Docker directly.
- Keep provider secrets out of manifests and API responses; provider keys should only exist in generated `domain.env` files.
- Tests should call public APIs, the launcher/TUI helpers, adapters, or public services (`tests/` uses API tests plus targeted `test_cli_*` modules).
- Do not add a new abstraction unless it hides real complexity.

