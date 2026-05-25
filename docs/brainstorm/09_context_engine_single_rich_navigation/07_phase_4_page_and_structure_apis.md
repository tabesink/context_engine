# 07 — Phase 4: Move Page and Structure APIs to Rich Structure Only

## Goal

Make page and structure APIs depend only on `DocumentProcessingRepository` and rich `DocumentStructure`.

---

# Page API

## Current Old Behavior

```text
GET /documents/{document_id}/pages/{page_number}
    └── DocumentRepository.get_parsed()
        └── parsed_documents.pages
```

## New Behavior

```text
GET /documents/{document_id}/pages/{page_number}
    └── DocumentProcessingRepository.get_page()
        └── document_pages
```

## Implementation Sketch

```python
@router.get("/{document_id}/pages/{page_number}")
def get_page(
    document_id: str,
    page_number: int,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PageResponse:
    DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )

    page = DocumentProcessingRepository(session).get_page(document_id, page_number)

    if not page:
        raise not_found("Page not found")

    return PageResponse(
        document_id=document_id,
        page_number=page.page_number,
        text=page.text or "",
        metadata=getattr(page, "metadata", {}) or {},
    )
```

## Page API Tests

```text
[ ] Authenticated user can read page from rich structure.
[ ] Admin can read page.
[ ] Missing page returns 404.
[ ] Missing document returns 404.
[ ] Unauthorized user cannot read page.
[ ] Endpoint does not require `parsed_documents`.
```

---

# Structure API

## Current Old Behavior

```text
GET /documents/{document_id}/structure
    ├── if rich structure exists:
    │     return rich structure
    └── else:
          fallback to navigation_indexes
```

## New Behavior

```text
GET /documents/{document_id}/structure
    ├── if rich structure exists:
    │     return rich structure
    └── else:
          404 Document structure not found
```

## Remove Fallback

Remove logic similar to:

```python
navigation = DocumentRepository(session).get_navigation_index(document_id)
if not navigation:
    raise not_found("Document structure not found")
return StructureResponse(document_id=document_id, tree=navigation.tree)
```

## Include Pages in `StructureResponse`

Recommended schema:

```python
class StructureResponse(BaseModel):
    document_id: str
    tree: list[dict]
    source: str = "document_structure"
    pages: list[dict] = []
    sections: list[dict] = []
    blocks: list[dict] = []
    source_chunks: list[dict] = []
    assets: list[dict] = []
```

Return:

```python
pages=[page.model_dump() for page in canonical.pages]
```

## Structure API Tests

```text
[ ] Rich structure returns `source="document_structure"`.
[ ] Response includes pages.
[ ] No fallback to `navigation_indexes`.
[ ] Missing rich structure returns 404.
```

## Acceptance Criteria

```text
[ ] Page API reads from `document_pages`.
[ ] Structure API reads from rich structure only.
[ ] No runtime fallback to old navigation index.
```
