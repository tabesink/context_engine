# Coding Agent Prompt: Add Context Engine Workspace Tree Endpoint

You are a senior backend engineer working in the `context_engine` repository.

Your task is to implement a native workspace-tree endpoint that supports the future WebUI.

## Goal

Add:

```http
GET /lightrag/domains/{domain_id}/workspace-tree
```

This endpoint must return all ready documents associated with the selected LightRAG domain and expand each document using the local Context Engine navigation structure: sections, pages, source chunks, and assets.

## Important architecture rule

Do not copy the Easy Deploy LightRAG server's conversation/source-tree snapshot model.

This workspace tree is not a per-query source tree. It is a full browser tree for the selected LightRAG domain.

## Current code anchors

Review these files before editing:

```text
app/main.py
app/api/routes/documents.py
app/api/routes/lightrag_admin.py
app/api/routes/admin.py
app/services/document_service.py
app/services/document_access_policy.py
app/storage/repositories/documents.py
app/storage/repositories/document_processing.py
app/storage/tables.py
app/schemas/documents.py
```

Key facts:

- `app/main.py` registers routers.
- `/lightrag/domains` already lists user-visible LightRAG domains.
- Admin upload accepts `lightrag_domain_id`.
- `DocumentService._upload_remote()` stores `metadata["lightrag"]["domain_id"]`.
- `DocumentRepository.list_ready()` lists ready documents but does not filter by LightRAG domain.
- `DocumentProcessingRepository.get_structure()` reconstructs pages, sections, blocks, source chunks, and assets.
- `app/api/routes/documents.py` already exposes document structure and detail endpoints.

## Files to add

```text
app/schemas/workspace_tree.py
app/services/workspace_tree_service.py
app/api/routes/workspace_tree.py
tests/test_workspace_tree_service.py
tests/test_workspace_tree_api.py
```

## Files to edit

```text
app/main.py
app/storage/repositories/documents.py
```

## Required implementation

1. Add Pydantic schemas:
   - `WorkspaceTreeNode`
   - `WorkspaceTreeResponse`

2. Add repository method:

```python
def list_ready_by_lightrag_domain(self, domain_id: str) -> list[DocumentRow]:
    ...
```

Use first-pass Python filtering over `document.meta["lightrag"]["domain_id"]` or fallback `document.meta["lightrag"]["domain"]`.

3. Add `WorkspaceTreeService`:

```python
class WorkspaceTreeService:
    def build_for_domain(self, *, domain_id: str, user: UserRow) -> WorkspaceTreeResponse:
        ...
```

The service must:

- Validate the domain exists using `LightRAGDomainService`.
- Load ready documents matching the domain.
- Load each document's local structure via `DocumentProcessingRepository.get_structure()`.
- Return a stable tree.
- Avoid full page/chunk text in the tree.
- Include references needed for WebUI click actions.

4. Add route:

```python
router = APIRouter(prefix="/lightrag/domains", tags=["workspace-tree"])

@router.get("/{domain_id}/workspace-tree")
def get_workspace_tree(...):
    ...
```

5. Register router in `app/main.py`.

6. Add tests.

## Expected response shape

```json
{
  "domain_id": "manuals",
  "display_name": "Manuals",
  "document_count": 1,
  "root": {
    "id": "domain:manuals",
    "kind": "domain",
    "title": "Manuals",
    "children": [
      {
        "id": "document:<document_id>",
        "kind": "document",
        "title": "Pump Manual.pdf",
        "document_id": "<document_id>",
        "status": "ready",
        "children": []
      }
    ]
  }
}
```

## Do not implement

- Do not add old `/api/v1/*` routes.
- Do not add conversation persistence.
- Do not add source-tree snapshot tables.
- Do not add graph write routes.
- Do not add a database migration in the first pass.
- Do not add a physical `lightrag_domain_id` column yet.
- Do not wire the WebUI yet.

## Test requirements

At minimum, test:

- Auth required.
- Unknown domain returns 404.
- Known empty domain returns empty root.
- Documents are filtered by domain.
- Not-ready documents are excluded.
- Section/page/chunk/asset references appear when structure exists.

## Completion criteria

The task is done when:

- Endpoint exists and is registered.
- Response follows the documented contract.
- Tests pass.
- No Easy Deploy compatibility routes were added.
- No frontend changes were made.
