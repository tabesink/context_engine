# 05 — Testing and Acceptance Criteria

## Backend tests

Add:

```text
tests/services/test_workspace_context_service.py
tests/api/test_workspace_context.py
```

### Service tests

#### 1. Parses valid node IDs

Expected:

- `domain:test` → kind `domain`, value `test`
- `document:doc1` → kind `document`, document `doc1`
- `section:doc1:sec1` → kind `section`, document `doc1`, value `sec1`
- `page:doc1:12` → kind `page`, document `doc1`, value `12`
- `chunk:doc1:abc` → kind `chunk`, document `doc1`, value `abc`
- `asset:doc1:fig1` → kind `asset`, document `doc1`, value `fig1`

Invalid IDs return 400.

#### 2. Domain node context

Input:

```text
node_id=domain:forging-kb
```

Expected:

- returns kind `domain`
- returns domain title
- includes domain metadata
- does not require document structure

#### 3. Document node context

Input:

```text
node_id=document:doc_123
```

Expected:

- enforces readable document access
- validates document belongs to selected domain
- returns document metadata
- returns structure counts when available
- returns safe text preview when available

#### 4. Section node context

Expected:

- returns section title
- returns page_start/page_end
- returns breadcrumb including document and section
- returns text from chunks in that section
- returns section assets

#### 5. Page node context

Expected:

- returns page number
- returns page metadata text or chunk fallback
- returns page assets

#### 6. Chunk node context

Expected:

- returns exact chunk text
- returns chunk_id
- returns page range
- returns referenced assets

#### 7. Asset node context

Expected:

- returns asset title/caption/type
- returns source URL and thumbnail URL
- returns nearby text

#### 8. Cross-domain document rejected

If document metadata says it belongs to `domain_a`, but endpoint path uses `domain_b`, return 404.

#### 9. Unreadable document rejected

If `DocumentAccessPolicy` says user cannot read document, return 404 or 403 according to existing project convention. Prefer 404 if the project wants to avoid leaking document existence.

#### 10. Missing structure handling

- document node can still return metadata
- child nodes return 404 if structure unavailable

## API tests

### Auth required

Unauthenticated request:

```http
GET /lightrag/domains/test/workspace-context?node_id=document:doc_123
```

Expected: 401.

### Valid document context

Authenticated request returns 200 and `WorkspaceSourceContext`.

### Invalid node ID

Expected: 400.

### Missing node

Expected: 404.

### Unavailable domain

Expected: existing domain registry error response.

## Retrieval response tests

Update retrieval schema/mapper tests to ensure evidence includes `workspace_node_id`.

Cases:

1. Metadata has `workspace_node_id` → preserve it.
2. Metadata has `chunk_id` → construct `chunk:{document_id}:{chunk_id}`.
3. Evidence has page_ref only → construct `page:{document_id}:{page_start}`.
4. No chunk/page → construct `document:{document_id}`.

## Frontend checks

No formal test framework may currently be configured. At minimum run:

```bash
cd client
npm run lint
npm run build
```

If component tests exist or are added, test:

1. `SidePanel` renders two tabs.
2. Context Stream tab shows existing context items.
3. Source Navigator tab shows empty state by default.
4. Loading source state is displayed.
5. Error source state is displayed.
6. Loaded source context renders breadcrumb, title, text, and assets.
7. Workspace tree click calls `onNodeSelect`.
8. Evidence card `Open source` calls the provided handler.

## Manual acceptance criteria

### A. Chat context stream still works

1. Open chat.
2. Select a domain.
3. Ask a question.
4. Right panel shows Context Stream.
5. Retrieved evidence appears.
6. Assistant response can be selected later and context updates accordingly.

Pass condition: no regression to existing retrieved-context display.

### B. Workspace-tree source navigator works

1. Open chat.
2. Select/load a domain with indexed documents.
3. Click a document/section/page/chunk/asset in the left workspace tree.
4. Right panel switches to Source Navigator.
5. Exact source context appears.

Pass condition: source context displays without sending a chat request.

### C. Tabs preserve state

1. Ask a question and view Context Stream.
2. Click a source and view Source Navigator.
3. Switch back to Context Stream.
4. Switch again to Source Navigator.

Pass condition: both tabs preserve their latest content.

### D. No silent retrieval filter

1. Click a source in the workspace tree.
2. Ask a normal question.

Pass condition: retrieval scope does not change unless a visible future filter control is explicitly used.

### E. Mobile behavior

1. Use narrow viewport.
2. Click a source.

Pass condition: side panel opens as overlay and Source Navigator tab is active.

## Definition of done

- Backend source-context endpoint implemented.
- Source context schemas added.
- Source context service added and tested.
- Retrieval evidence includes `workspace_node_id`.
- Frontend source context API client added.
- Side panel has two tabs.
- Workspace tree click opens Source Navigator.
- Existing chat retrieval context still works.
- No direct frontend calls to LightRAG are introduced.
- `npm run lint` and `npm run build` pass for client.
- Backend tests pass.
