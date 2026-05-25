# Implementation Plan: Native Workspace Tree Endpoint for `context_engine`

## 1. Objective

Implement a native `workspace-tree` endpoint in `context_engine` so the future WebUI can display all documents associated with a selected LightRAG domain, with each document expanded using Context Engine's local navigation structure.

Target endpoint:

```http
GET /lightrag/domains/{domain_id}/workspace-tree
```

Target visual model:

```text
Workspace Tree Root
└── LightRAG Domain: <domain_id>
    ├── Document A
    │   ├── Section 1
    │   │   ├── Page 1
    │   │   ├── Chunk 1
    │   │   └── Asset 1
    │   └── Section 2
    └── Document B
        └── ...
```

## 2. Current Context Engine evidence

Use these current code surfaces as the implementation anchors.

| Existing capability | File / function | Why it matters |
|---|---|---|
| Router registration | `app/main.py -> create_app()` | New route module must be included here. |
| User auth dependency | `app.api.deps.get_current_user` | Workspace tree should require an authenticated user. |
| User domain listing | `app/api/routes/lightrag_admin.py -> list_user_domains()` | Confirms user-facing domain listing already exists at `/lightrag/domains`. |
| Admin document upload domain parameter | `app/api/routes/admin.py -> upload_document(..., lightrag_domain_id: Form(...))` | Confirms uploads are already domain-aware. |
| Document metadata stores LightRAG domain | `app/services/document_service.py -> _upload_remote()` | Stores `metadata["lightrag"]["domain_id"]`. |
| Readable documents policy | `app/services/document_access_policy.py -> list_readable_documents()` | Current read rule: authenticated users can read ready documents. |
| Document list | `app/storage/repositories/documents.py -> list_ready()` | Currently lists ready docs but does not filter by LightRAG domain. |
| Document structure endpoint | `app/api/routes/documents.py -> get_structure()` | Existing API already reconstructs sections/pages/chunks/assets. |
| Structure repository | `app/storage/repositories/document_processing.py -> get_structure()` | Primary data source for sections, pages, blocks, chunks, assets. |
| Tables | `app/storage/tables.py` | Existing tables include `documents`, `document_sections`, `document_pages`, `document_blocks`, `document_source_chunks`, `document_assets`. |

### Current app-state summary

As of the current `app` implementation:

- `app/main.py` registers the existing route modules, but there is no workspace-tree route yet.
- `GET /lightrag/domains` already provides the user-safe domain picker shape: `id`, `display_name`, `is_healthy`, and `is_default`.
- Admin upload already records `metadata["lightrag"]["domain_id"]`; retrieval also validates selected `document_ids` against `lightrag_domain_id`.
- `DocumentProcessingRepository.get_structure()` reconstructs the local navigation model from existing tables.
- `app/api/routes/documents.py` exposes detail routes for documents, sections, pages, chunks, assets, and asset thumbnails. The workspace tree should point to these routes instead of inlining content.
- The current access policy is intentionally simple: any authenticated user may read READY documents.

### Areas of tension and design choke points

These are the main points to keep visible while implementing:

- Static workspace tree vs chat source tree: the lifted WebUI has a per-turn `SourceTreeSnapshot` model, but this endpoint is a domain browser. Keep them separate; a future frontend adapter can transform or combine them.
- Domain identity: Context Engine uses LightRAG domain IDs from the manifest. Do not introduce host-port identity or Easy Deploy route compatibility.
- Metadata filtering: domain membership currently lives in document JSON metadata, not a column. Python filtering over `list_ready()` is acceptable for this pass; add an indexed column only when scale proves it is needed.
- Tree construction ownership: `_section_tree()` is currently route-local in `documents.py`. Keep workspace tree-building inside a service for now; extract shared helpers later only if there is real reuse pressure.
- Payload size: `get_structure()` can load full page and chunk text. The workspace tree must return reference nodes and short labels only.
- N+1 structure reads: the first pass will call `get_structure()` once per ready document in a domain. Treat this as a known scaling choke point, not a reason to add a batch repository prematurely.
- Partial structure quality: a document with missing or weak structure should still appear in the tree with `metadata.structure_available = false`.

## 3. Design decision

Build a new native Context Engine endpoint, not an Easy Deploy compatibility endpoint.

Recommended:

```http
GET /lightrag/domains/{domain_id}/workspace-tree
```

Avoid:

```http
GET /api/conversations/{conversation_id}/source-tree
GET /api/lightrag/domains/{port}/workspace-tree
```

Reason:

- Context Engine uses domain IDs, not ports.
- Workspace tree is a full domain browser, not a per-query retrieval-source snapshot.
- The tree should come from local navigation tables, not from LightRAG retrieval result chunks.

## 4. Scope for first implementation

### In scope

- Add workspace-tree Pydantic schemas.
- Add workspace-tree service.
- Add workspace-tree API route.
- Add repository helper to list ready documents by LightRAG domain.
- Validate the requested domain exists.
- Require authentication.
- Return only documents readable by the authenticated user.
- Include sections, pages, chunks, and assets as tree nodes.
- Keep response stable for WebUI rendering.
- Add unit/API tests.

### Out of scope for first implementation

- Persistent chat conversations.
- Source-tree snapshots.
- Graph editing.
- Frontend/WebUI wiring.
- Changing upload behavior.
- Adding a physical `lightrag_domain_id` DB column.
- Complex database JSONB filtering.
- Full-text document search in the tree.
- Per-user document ACLs beyond the existing shared-corpus ready-document policy.

## 5. Recommended files to add

```text
app/schemas/workspace_tree.py
app/services/workspace_tree_service.py
app/api/routes/workspace_tree.py
tests/test_workspace_tree_service.py
tests/test_workspace_tree_api.py
```

## 6. Recommended files to edit

```text
app/main.py
app/storage/repositories/documents.py
```

Optional later:

```text
app/api/routes/lightrag_admin.py
```

Only edit `lightrag_admin.py` later if you prefer mounting the route in that existing module instead of creating a dedicated `workspace_tree.py` route module. A dedicated route module is cleaner for junior developers.

## 7. Schema design

Create `app/schemas/workspace_tree.py`.

Recommended DTOs:

```python
from typing import Literal
from pydantic import BaseModel, Field

WorkspaceTreeNodeKind = Literal[
    "domain",
    "document",
    "section",
    "page",
    "chunk",
    "asset",
]

class WorkspaceTreeNode(BaseModel):
    id: str
    kind: WorkspaceTreeNodeKind
    title: str
    children: list["WorkspaceTreeNode"] = Field(default_factory=list)

    # Common optional metadata for WebUI actions.
    document_id: str | None = None
    section_id: str | None = None
    page_number: int | None = None
    chunk_id: str | None = None
    asset_id: str | None = None

    # Display/status metadata.
    status: str | None = None
    filename: str | None = None
    content_type: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    asset_type: str | None = None
    thumbnail_url: str | None = None
    metadata: dict = Field(default_factory=dict)

class WorkspaceTreeResponse(BaseModel):
    domain_id: str
    display_name: str | None = None
    document_count: int
    root: WorkspaceTreeNode
```

Important:

- Use string IDs that are globally stable enough for frontend tree rendering.
- Prefix IDs by kind:
  - `domain:{domain_id}`
  - `document:{document_id}`
  - `section:{document_id}:{section_id}`
  - `page:{document_id}:{page_number}`
  - `chunk:{document_id}:{chunk_id}`
  - `asset:{document_id}:{asset_id}`

## 8. Repository helper

Add a small helper to `app/storage/repositories/documents.py`.

Recommended first-pass implementation:

```python
def list_ready_by_lightrag_domain(self, domain_id: str) -> list[DocumentRow]:
    documents = self.list_ready()
    matched: list[DocumentRow] = []
    for document in documents:
        metadata = document.meta if isinstance(document.meta, dict) else {}
        lightrag = metadata.get("lightrag") if isinstance(metadata.get("lightrag"), dict) else {}
        document_domain_id = lightrag.get("domain_id") or lightrag.get("domain")
        if document_domain_id == domain_id:
            matched.append(document)
    return matched
```

Why this is acceptable for first pass:

- It is simple and database-portable.
- It avoids JSONB-specific SQLAlchemy expressions.
- It uses existing metadata shape.
- It keeps the migration surface zero.

Later optimization:

- Add a real `documents.lightrag_domain_id` column with an index.
- Backfill from `documents.metadata.lightrag.domain_id`.
- Replace Python filtering with indexed SQL filtering.

Do not add the column in the first pass unless the project already has many thousands of documents.

## 9. Service design

Create `app/services/workspace_tree_service.py`.

Recommended responsibilities:

1. Validate requested LightRAG domain exists.
2. Load ready documents for that domain.
3. Respect current document access policy.
4. For each document, load canonical local navigation structure.
5. Convert the structure into tree nodes.
6. Return `WorkspaceTreeResponse`.

Service sketch:

```python
from sqlalchemy.orm import Session

from app.lightrag_deploy.errors import DomainNotFoundError
from app.lightrag_deploy.service import LightRAGDomainService
from app.schemas.workspace_tree import WorkspaceTreeNode, WorkspaceTreeResponse
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.tables import UserRow

class WorkspaceTreeService:
    def __init__(self, session: Session, domain_service: LightRAGDomainService | None = None):
        self.session = session
        self.documents = DocumentRepository(session)
        self.processing = DocumentProcessingRepository(session)
        self.domain_service = domain_service or LightRAGDomainService()

    def build_for_domain(self, *, domain_id: str, user: UserRow) -> WorkspaceTreeResponse:
        domain = self._domain_or_404(domain_id)
        documents = self.documents.list_ready_by_lightrag_domain(domain_id)

        # V1 policy: shared corpus. User is accepted for future ACL compatibility.
        del user

        document_nodes = [self._document_node(document) for document in documents]
        root = WorkspaceTreeNode(
            id=f"domain:{domain_id}",
            kind="domain",
            title=domain.display_name or domain.id,
            children=document_nodes,
            metadata={"is_healthy": domain.is_healthy, "is_default": domain.is_default},
        )
        return WorkspaceTreeResponse(
            domain_id=domain_id,
            display_name=domain.display_name,
            document_count=len(document_nodes),
            root=root,
        )
```

The exact implementation can differ, but keep these responsibilities separate from the route.

## 10. Route design

Create `app/api/routes/workspace_tree.py`.

Recommended route:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.schemas.workspace_tree import WorkspaceTreeResponse
from app.services.workspace_tree_service import WorkspaceTreeService
from app.storage.db import get_session
from app.storage.tables import UserRow

router = APIRouter(prefix="/lightrag/domains", tags=["workspace-tree"])

@router.get("/{domain_id}/workspace-tree")
def get_workspace_tree(
    domain_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> WorkspaceTreeResponse:
    return WorkspaceTreeService(session).build_for_domain(domain_id=domain_id, user=user)
```

Then update `app/main.py`:

```python
from app.api.routes import workspace_tree

# inside create_app()
app.include_router(workspace_tree.router)
```

## 11. Tree construction algorithm

### Document node

For each ready document matching the domain:

```text
document node
  -> section tree if sections exist
  -> fallback pages if no sections exist
  -> optional loose chunks/assets if not attached to sections/pages
```

Document node fields:

```python
WorkspaceTreeNode(
    id=f"document:{document.id}",
    kind="document",
    title=document.filename,
    document_id=document.id,
    status=document.status,
    filename=document.filename,
    content_type=document.content_type,
    children=[...],
    metadata={"created_at": ..., "updated_at": ...},
)
```

### Section nodes

Use `DocumentSection.parent_section_id` to construct hierarchy.

Each section node should include:

```text
section_id
title
level
page_start
page_end
```

Attach page nodes under a section if the page number is inside the section page range.

### Page nodes

Each page node should include:

```text
page_number
title = "Page {page_number}"
```

Attach chunks/assets to pages if they are not already represented under a section or if the UI wants page-level browsing.

### Chunk nodes

Chunk node fields:

```text
chunk_id
page_start
page_end
short title/snippet
```

Recommended title:

```python
snippet = chunk.text.strip().replace("\n", " ")[:80]
title = snippet or f"Chunk {chunk.chunk_id}"
```

Do not return full chunk text in the tree by default. The WebUI can fetch chunk details from:

```http
GET /documents/{document_id}/chunks/{chunk_id}
```

### Asset nodes

Asset node fields:

```text
asset_id
asset_type
page_number
caption
thumbnail_url
```

Recommended thumbnail URL:

```text
/documents/{document_id}/assets/{asset_id}/thumbnail
```

Do not inline binary image data in the tree response.

## 12. Fallback behavior

Use deterministic fallback behavior:

| Case | Behavior |
|---|---|
| Domain does not exist | `404 Not Found` |
| Domain exists but no documents are ready | Return root with empty `children` and `document_count = 0` |
| Document has no local structure | Return document node with empty `children` and metadata flag `structure_available = false` |
| Document has pages but no sections | Use pages directly under document |
| Document has chunks but no sections/pages | Use chunks directly under document |
| Document has assets with no section/page | Add under document as loose asset nodes |

Do not fail the entire workspace tree because one document has missing structure.

## 13. Permission model

Use the current V1 policy:

```text
Any authenticated user can read ready documents.
```

Do not add admin-only access to the workspace tree unless the product decision changes.

Do not return documents that are:

```text
uploaded
indexing
failed
deleted
```

Unless an admin-specific tree endpoint is later requested.

## 14. Low-entropy constraints

A junior developer should follow these constraints:

- Do not add a new database table.
- Do not add a migration in the first pass.
- Do not copy Easy Deploy's `source_tree_snapshots` table or model.
- Do not expose LightRAG host ports in the WebUI tree contract.
- Do not make the WebUI call `/documents/{id}/structure` repeatedly to build the initial tree.
- Do not inline full page text or full chunk text in the tree.
- Do not include binary assets in the JSON response.
- Do not change document upload behavior unless tests prove `domain_id` metadata is missing.

## 15. Implementation sequence

### Step 1 — Add schemas

Add `app/schemas/workspace_tree.py`.

Run type checks/import checks.

### Step 2 — Add repository helper

Add `DocumentRepository.list_ready_by_lightrag_domain(domain_id)`.

Write unit tests for metadata matching:

- `metadata.lightrag.domain_id`
- `metadata.lightrag.domain`
- missing `lightrag`
- wrong domain
- non-ready document excluded via `list_ready()`

### Step 3 — Add service

Add `WorkspaceTreeService`.

Implement:

- `build_for_domain()`
- `_domain_or_404()`
- `_document_node()`
- `_section_nodes()`
- `_page_node()`
- `_chunk_node()`
- `_asset_node()`

### Step 4 — Add API route

Add `app/api/routes/workspace_tree.py`.

Update `app/main.py`.

### Step 5 — Add API tests

Test:

- unauthenticated request returns auth error
- unknown domain returns 404
- known empty domain returns empty root
- known domain with one document returns document node
- document sections appear under document
- page/chunk/asset references are present

### Step 6 — Run full test suite

Run existing backend tests and new tests.

### Step 7 — Document endpoint for WebUI

Add short docs to repo documentation:

```text
docs/workspace-tree.md
```

Include response example and frontend click behavior.

## 16. Acceptance criteria

The implementation is complete when:

- `GET /lightrag/domains/{domain_id}/workspace-tree` exists.
- It requires authentication.
- It validates domain ID.
- It returns only ready documents belonging to the selected domain.
- It uses existing local navigation structure.
- It returns stable node IDs.
- It returns document, section, page, chunk, and asset nodes when available.
- It does not return full chunk/page text by default.
- It returns an empty tree for valid domains with no documents.
- It has tests for success, empty, missing-domain, and auth cases.
- `app/main.py` includes the router.
- No old Easy Deploy `/api/...` compatibility routes are added.

## 17. Future enhancements

Do these later, only after the WebUI is wired:

- Add query params:
  - `include_chunks=true|false`
  - `include_assets=true|false`
  - `max_depth=document|section|page|chunk|asset`
- Add search/filter support.
- Add indexed `documents.lightrag_domain_id` column.
- Add admin tree that includes indexing/failed documents.
- Add tree node counts.
- Add source-tree snapshot per chat answer if saved chat history is added.
