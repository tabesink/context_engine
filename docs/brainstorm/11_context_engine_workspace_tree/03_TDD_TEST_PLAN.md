# TDD Test Plan: Workspace Tree Endpoint

## Test file targets

Add:

```text
tests/test_workspace_tree_service.py
tests/test_workspace_tree_api.py
```

Reuse existing test fixtures where possible. Do not create a large custom test harness if the repo already has test helpers for authenticated users, admins, database sessions, or test clients.

## TDD posture

Use vertical tracer bullets rather than writing a broad imagined suite first:

1. Prove the public HTTP path exists and enforces auth.
2. Prove domain validation and the empty-domain response.
3. Prove domain filtering over existing document metadata.
4. Prove one real structure node path at a time: section, page, chunk, asset.

Prefer tests through `TestClient` and the service's public `build_for_domain()` behavior. Mock only the LightRAG domain-service boundary when needed; do not mock repositories owned by this app unless the test is explicitly about route error mapping.

## 1. Repository helper tests

Target:

```python
DocumentRepository.list_ready_by_lightrag_domain(domain_id)
```

### Test cases

| Test | Setup | Expected |
|---|---|---|
| includes document with `metadata.lightrag.domain_id` | ready doc, metadata domain `manuals` | returned |
| includes document with fallback `metadata.lightrag.domain` | ready doc, metadata domain `manuals` | returned |
| excludes wrong domain | ready doc, metadata domain `policies` | not returned |
| excludes missing metadata | ready doc, no `lightrag` metadata | not returned |
| excludes not-ready documents | indexing/failed/deleted doc with correct domain | not returned |

## 2. Service tests

Target:

```python
WorkspaceTreeService.build_for_domain(domain_id=..., user=...)
```

### Test: valid empty domain

Setup:

- Fake or test domain service returns domain `manuals`.
- No ready documents match `manuals`.

Expected:

- Response `domain_id == "manuals"`.
- `document_count == 0`.
- Root kind is `domain`.
- Root children is empty list.

This should be the first service tracer bullet after the route/auth smoke test because it establishes the response contract without needing document-structure setup.

### Test: one document with no structure

Setup:

- Ready document has `metadata.lightrag.domain_id == "manuals"`.
- No rows in document structure tables.

Expected:

- Response has one document child.
- Document node has `metadata.structure_available == false`.
- No exception is raised.

### Test: one document with sections

Setup:

- Ready document in domain `manuals`.
- Add one parent section and one child section.

Expected:

- Document node has section child.
- Parent section has child section.
- IDs are stable and prefixed.

### Test: pages are included

Setup:

- Ready document in domain `manuals`.
- Add page rows.

Expected:

- Page nodes appear under the relevant section or document fallback.
- `page_number` is set.

### Test: chunks are included as references

Setup:

- Ready document in domain `manuals`.
- Add a source chunk row.

Expected:

- Chunk node appears.
- `chunk_id` is set.
- Full chunk text is not included in the node.

Also assert the node title is only a short display label/snippet, not a full content payload.

### Test: assets are included as references

Setup:

- Ready document in domain `manuals`.
- Add an asset row with thumbnail path.

Expected:

- Asset node appears.
- `asset_id` is set.
- `thumbnail_url` points to `/documents/{document_id}/assets/{asset_id}/thumbnail`.
- No binary data is included.

### Test: unknown domain

Setup:

- Domain service raises `DomainNotFoundError` for `missing`.

Expected:

- Service or route maps this to 404.

## 3. API tests

Target:

```http
GET /lightrag/domains/{domain_id}/workspace-tree
```

### Test: unauthenticated request fails

Request without token.

Expected:

- 401 or same auth failure shape as other protected routes.

This should be the first API tracer bullet because it proves router registration, path shape, and dependency wiring.

### Test: authenticated valid domain returns tree

Request with user token.

Expected:

- 200.
- JSON contains `domain_id`.
- JSON contains `root.kind == "domain"`.
- JSON contains `document_count`.

### Test: unknown domain returns 404

Request valid auth but invalid domain.

Expected:

- 404.

### Test: documents are filtered by domain

Setup:

- One document in domain `manuals`.
- One document in domain `policies`.

Request:

```http
GET /lightrag/domains/manuals/workspace-tree
```

Expected:

- Only `manuals` document appears.

Also include the fallback metadata key `metadata.lightrag.domain` in a repository or service-level test so the API contract does not depend on legacy metadata forever.

### Test: not-ready documents are not shown

Setup:

- One `INDEXING` document in domain `manuals`.
- One `READY` document in domain `manuals`.

Expected:

- Only ready document appears.

## 4. Regression tests to avoid

Do not write brittle tests that require exact full JSON response ordering unless ordering is part of the API contract.

Stable ordering recommendation:

- Documents: current repository order, usually newest first.
- Sections: group by parent and preserve existing repository order.
- Pages: ascending page number.
- Chunks: repository order or page_start order if easy to apply.
- Assets: repository order or page_number order if easy to apply.

## 5. Acceptance test example

Pseudo-test:

```python
def test_workspace_tree_returns_domain_documents(client, auth_headers, session):
    # arrange
    create_domain_manifest_with_domain("manuals")
    document = create_ready_document(
        session,
        filename="Pump Manual.pdf",
        metadata={"lightrag": {"domain_id": "manuals"}},
    )
    create_section(session, document_id=document.id, section_id="intro", title="Introduction")
    create_page(session, document_id=document.id, page_number=1)

    # act
    response = client.get(
        "/lightrag/domains/manuals/workspace-tree",
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain_id"] == "manuals"
    assert payload["document_count"] == 1
    document_node = payload["root"]["children"][0]
    assert document_node["kind"] == "document"
    assert document_node["document_id"] == document.id
```
