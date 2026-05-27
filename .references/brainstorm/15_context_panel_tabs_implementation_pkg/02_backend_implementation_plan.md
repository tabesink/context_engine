# 02 — Backend Implementation Plan

## Current backend anchor points

The current backend already includes:

- `app/main.py` registering `workspace_tree.router`.
- `app/api/routes/workspace_tree.py` exposing `GET /lightrag/domains/{domain_id}/workspace-tree`.
- `app/schemas/workspace_tree.py` with `WorkspaceTreeNode` and node kinds: `domain`, `document`, `section`, `page`, `chunk`, `asset`.
- `app/services/workspace_tree_service.py` building tree nodes using `DocumentRepository`, `DocumentProcessingRepository`, `DocumentAccessPolicy`, and `LightRAGDomainRegistry`.
- `app/schemas/retrieval.py` with `EvidenceResponse` and `AssetResponse`.
- `app/retrieval/evidence_mapper.py` already mapping `source_path`, `document_title`, `chunk_id`, and `reference_id` from evidence metadata.

The new implementation should extend these existing pieces rather than creating a separate source/document browser system.

## Backend objective

Add a read-only source-inspection endpoint that converts a workspace-tree node ID into exact display-ready source context.

Recommended endpoint:

```http
GET /lightrag/domains/{domain_id}/workspace-context?node_id=<url-encoded-node-id>
```

Why query parameter instead of path segment?

- Existing node IDs contain colons, for example `chunk:{document_id}:{chunk_id}`.
- Query parameters avoid path encoding edge cases and make frontend calls simpler.

## New schema file

Add:

```text
app/schemas/workspace_context.py
```

Recommended schemas:

```py
from typing import Literal
from pydantic import BaseModel, Field

WorkspaceContextNodeKind = Literal["domain", "document", "section", "page", "chunk", "asset"]

class WorkspaceContextBreadcrumbItem(BaseModel):
    id: str | None = None
    kind: WorkspaceContextNodeKind | str
    title: str

class WorkspaceContextDocument(BaseModel):
    document_id: str
    title: str
    filename: str | None = None
    content_type: str | None = None
    status: str | None = None
    source_path: str | None = None

class WorkspaceContextAsset(BaseModel):
    asset_id: str
    document_id: str
    asset_type: str
    title: str
    caption: str | None = None
    page_number: int | None = None
    section_id: str | None = None
    url: str | None = None
    thumbnail_url: str | None = None
    mime_type: str | None = None
    metadata: dict = Field(default_factory=dict)

class WorkspaceSourceContext(BaseModel):
    node_id: str
    kind: WorkspaceContextNodeKind
    title: str
    domain_id: str
    breadcrumb: list[WorkspaceContextBreadcrumbItem] = Field(default_factory=list)
    document: WorkspaceContextDocument | None = None
    section_id: str | None = None
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    chunk_id: str | None = None
    asset_id: str | None = None
    summary: str | None = None
    text: str | None = None
    assets: list[WorkspaceContextAsset] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
```

## New service file

Add:

```text
app/services/workspace_context_service.py
```

Constructor should mirror `WorkspaceTreeService`:

```py
class WorkspaceContextService:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        processing: DocumentProcessingRepository,
        domain_registry: LightRAGDomainRegistry,
    ):
        self.documents = documents
        self.processing = processing
        self.domain_registry = domain_registry
```

Main method:

```py
def build_for_node(self, *, domain_id: str, node_id: str, user: UserRow) -> WorkspaceSourceContext:
    domain = self.domain_registry.validate_available(domain_id)
    parsed = parse_workspace_node_id(node_id)
    # resolve document if applicable
    # enforce DocumentAccessPolicy
    # enforce document belongs to domain_id
    # load document structure
    # delegate by node kind
```

## Node ID parser

Add a small parser function in the service or a helper module:

```py
@dataclass(frozen=True)
class ParsedWorkspaceNodeId:
    kind: str
    document_id: str | None = None
    value: str | None = None


def parse_workspace_node_id(node_id: str) -> ParsedWorkspaceNodeId:
    parts = node_id.split(":", 2)
    kind = parts[0]

    if kind == "domain" and len(parts) == 2:
        return ParsedWorkspaceNodeId(kind="domain", value=parts[1])

    if kind == "document" and len(parts) == 2:
        return ParsedWorkspaceNodeId(kind="document", document_id=parts[1])

    if kind in {"section", "page", "chunk", "asset"} and len(parts) == 3:
        return ParsedWorkspaceNodeId(kind=kind, document_id=parts[1], value=parts[2])

    raise HTTPException(status_code=400, detail="Invalid workspace node id")
```

If document IDs or chunk IDs can contain colons, replace this with base64url-safe IDs later. For now, match the current workspace-tree ID format.

## Document/domain validation

For any node tied to a document:

1. Load document by ID.
2. Return 404 if missing.
3. Check current user can read it via `DocumentAccessPolicy`.
4. Check document belongs to requested `domain_id` using the same metadata convention used elsewhere:

```py
metadata = document.meta if isinstance(document.meta, dict) else {}
lightrag = metadata.get("lightrag", {}) if isinstance(metadata.get("lightrag"), dict) else {}
document_domain_id = lightrag.get("domain_id") or lightrag.get("domain")
```

If mismatch, return 404 rather than 403 to avoid leaking document existence across domains.

## Structure lookup

Use existing processing repository:

```py
structure = self.processing.get_structure(document.id, source_file=document.storage_path)
```

Handle `structure is None` gracefully:

- document node: still return document metadata
- section/page/chunk/asset node: return 404 or a response with `summary="Document structure is unavailable"`

Recommendation: return 404 for child node if structure is unavailable, because the node cannot be resolved reliably.

## Node-specific builders

### Domain node

For `domain:{domain_id}`:

- validate domain
- return domain summary
- no document required
- optional metadata: `is_healthy`, `is_default`

### Document node

For `document:{document_id}`:

Return:

- filename/title
- content type
- status
- source path
- summary of structure availability
- counts: sections/pages/chunks/assets if structure exists
- first useful text preview from first chunk or first page metadata text

### Section node

For `section:{document_id}:{section_id}`:

Return:

- section title
- page range
- section breadcrumb if parent section data exists
- text preview by concatenating chunks with matching `section_id`
- assets with matching `section_id`

### Page node

For `page:{document_id}:{page_number}`:

Return:

- page number
- page-level metadata
- text from page metadata if available
- fallback to chunks whose range includes that page
- assets on that page

### Chunk node

For `chunk:{document_id}:{chunk_id}`:

Return:

- exact chunk text
- page range
- section title if matching section exists
- assets referenced by `chunk.asset_ids`

### Asset node

For `asset:{document_id}:{asset_id}`:

Return:

- asset caption/title/type
- URL and thumbnail URL using existing document asset route pattern
- page/section metadata
- nearby text from page, section chunks, or related chunks

## Route implementation

Modify:

```text
app/api/routes/workspace_tree.py
```

Add import:

```py
from app.schemas.workspace_context import WorkspaceSourceContext
from app.services.workspace_context_service import WorkspaceContextService
```

Add endpoint:

```py
@router.get("/{domain_id}/workspace-context")
def get_workspace_context(
    domain_id: str,
    node_id: str = Query(..., min_length=1),
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
    domain_registry: LightRAGDomainRegistry = Depends(get_domain_registry),
) -> WorkspaceSourceContext:
    service = WorkspaceContextService(
        documents=DocumentRepository(session),
        processing=DocumentProcessingRepository(session),
        domain_registry=domain_registry,
    )
    try:
        return service.build_for_node(domain_id=domain_id, node_id=node_id, user=user)
    except LightRAGDomainRegistryError as exc:
        raise lightrag_domain_http_exception(exc) from exc
```

## Retrieval response improvement

Add `workspace_node_id` to retrieved evidence so evidence cards can open the same source navigator endpoint.

Modify:

```text
app/schemas/retrieval.py
```

```py
class EvidenceResponse(BaseModel):
    ...
    workspace_node_id: str | None = None
```

Modify:

```text
app/retrieval/evidence_mapper.py
```

Recommended mapping priority:

```py
workspace_node_id = metadata.get("workspace_node_id")
if not workspace_node_id and metadata.get("chunk_id"):
    workspace_node_id = f"chunk:{evidence.document_id}:{metadata['chunk_id']}"
elif not workspace_node_id and evidence.page_ref and evidence.page_ref.page_start:
    workspace_node_id = f"page:{evidence.document_id}:{evidence.page_ref.page_start}"
elif not workspace_node_id:
    workspace_node_id = f"document:{evidence.document_id}"
```

Then include `workspace_node_id=workspace_node_id` in the response.

## Security and access control

- Require `get_current_user` for the source context endpoint.
- Reuse `DocumentAccessPolicy` before returning any document-tied context.
- For inaccessible or cross-domain documents, return 404.
- Do not expose filesystem paths beyond existing safe `source_path`/asset URLs.
- Do not expose raw provider secrets or LightRAG deployment internals.

## Backend test plan

Add tests around:

```text
tests/api/test_workspace_context.py
tests/services/test_workspace_context_service.py
```

Required cases:

1. Authenticated user can inspect domain node.
2. Authenticated user can inspect readable document node.
3. Section node returns section title, page range, and text preview.
4. Page node returns page number and nearby text.
5. Chunk node returns exact chunk text.
6. Asset node returns asset URLs and associated caption/page.
7. Missing node returns 404.
8. Invalid node ID returns 400.
9. Document from another domain returns 404.
10. User without access receives 404/403 according to existing project convention.
11. Archived/unhealthy domain uses existing domain registry error behavior.

## Do not do this

Do not:

- call LightRAG directly from the frontend
- implement a second workspace-tree service
- reuse chat retrieval endpoint for deterministic source inspection
- overload `ContextPanelItem[]` with source navigator state
- silently set retrieval filters when a source is clicked
