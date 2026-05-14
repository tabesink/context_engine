# Junior Developer Start Here

This backend lets authenticated users ask questions over uploaded documents. Admins upload and index documents. Normal users query ready documents.

## The Short Version

The system has one API-facing response contract called `Evidence`.

Evidence can come from:

- Local semantic retrieval over indexed chunks.
- Local navigation retrieval over pages, sections, and document structure.
- Remote LightRAG retrieval when `LIGHTRAG_ENABLED=true`.

LightRAG is optional and external. The default local path still works without a running LightRAG service.

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
10. `app/retrieval/router.py`
11. `app/retrieval/semantic_engine.py`
12. `app/retrieval/navigation_engine.py`
13. `app/integrations/lightrag_remote_adapter.py`
14. `app/integrations/lightrag_domains.py`
15. `app/integrations/pageindex_adapter.py`
16. `app/workers/tasks.py`
17. `cli/main.py`

## Important Words

- `Document`: uploaded source file and metadata.
- `ParsedDocument`: normalized page/section text extracted from a document.
- `Evidence`: a retrieved piece of text the answer is allowed to use.
- `RetrievalMode`: `semantic`, `navigation`, `hybrid`, or `auto`.
- `Job`: background indexing work run by the worker.
- `LightRAGRemoteAdapter`: HTTP boundary to an external LightRAG service.
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

Query:

```text
user -> /query -> RetrievalService -> local router or remote LightRAG -> evidence -> answer composer
```

Graph reads:

```text
user -> /graphs or /graph/label/... -> LightRAGRemoteAdapter -> external LightRAG
```

## Rules of Thumb

- Routes should be thin. Put behavior in services.
- Services should not know third-party library details.
- Retrieval engines and adapters should return `Evidence`, never raw external objects.
- Keep LightRAG communication HTTP-only inside `app/integrations/lightrag_remote_adapter.py`.
- Tests should call public APIs, CLI commands, adapters, or public services.
- Do not add a new abstraction unless it hides real complexity.

