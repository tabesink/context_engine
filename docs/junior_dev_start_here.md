# Junior Developer Start Here

This backend lets authenticated users ask questions over uploaded documents. Admins upload and index documents. Normal users query ready documents.

## The Short Version

The system has two retrieval engines:

- Semantic retrieval finds meaning across chunks and documents.
- Navigation retrieval finds exact pages, sections, and document structure.

The API combines them behind one response format called `Evidence`.

## Read Files in This Order

1. `docs/implementation-plan.md`
2. `docs/architecture.md`
3. `app/main.py`
4. `app/domain/models.py`
5. `app/schemas/query.py`
6. `app/api/routes/query.py`
7. `app/services/retrieval_service.py`
8. `app/retrieval/router.py`
9. `app/retrieval/semantic_engine.py`
10. `app/retrieval/navigation_engine.py`
11. `app/integrations/lightrag_adapter.py`
12. `app/integrations/pageindex_adapter.py`
13. `app/workers/tasks.py`

## Important Words

- `Document`: uploaded source file and metadata.
- `ParsedDocument`: normalized page/section text extracted from a document.
- `Evidence`: a retrieved piece of text the answer is allowed to use.
- `RetrievalMode`: `semantic`, `navigation`, `hybrid`, or `auto`.
- `Job`: background indexing work run by the worker.
- `Admin`: user who can mutate documents and indexes.
- `User`: authenticated user who can query ready documents.

## Common Flows

Admin upload:

```text
admin -> /admin/documents/upload -> file storage -> document row -> indexing job
```

Indexing:

```text
worker -> parser -> navigation index -> semantic index -> document ready
```

Query:

```text
user -> /query -> retrieval router -> engines -> evidence -> answer composer
```

## Rules of Thumb

- Routes should be thin. Put behavior in services.
- Services should not know third-party library details.
- Retrieval engines should return `Evidence`, never raw adapter objects.
- Tests should call public APIs or public services.
- Do not add a new abstraction unless it hides real complexity.

