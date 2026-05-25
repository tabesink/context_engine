# 02 — Phase: Persist `DocumentPage`

## Goal

Persist `DocumentPage` as part of rich `DocumentStructure`.

## Files to Inspect/Change

```text
app/document_processing/models.py
app/storage/tables.py
app/storage/repositories/document_processing.py
alembic/versions/<revision>_add_document_pages.py
tests/storage/test_document_processing_repository.py
```

## Add or Verify `DocumentPageRow`

Example shape:

```python
class DocumentPageRow(Base):
    __tablename__ = "document_pages"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer, index=True)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", json_type(), default=dict)
```

Recommended uniqueness:

```text
UNIQUE(document_id, page_number)
```

Recommended ID:

```text
{document_id}:page:{page_number}
```

## Add or Verify `DocumentPage.metadata`

```python
metadata: dict = Field(default_factory=dict)
```

## Repository Behavior

`save_structure()` should delete and replace pages for a document.

Delete order:

```python
for table in (
    DocumentAssetRow,
    DocumentSourceChunkRow,
    DocumentBlockRow,
    DocumentSectionRow,
    DocumentPageRow,
):
    self.session.execute(delete(table).where(table.document_id == document_id))
```

Save:

```python
for page in structure.pages:
    self.session.add(self._page_row(structure.document_id, page))
```

Load:

```python
pages = [
    self._page_model(row)
    for row in self.session.scalars(
        select(DocumentPageRow)
        .where(DocumentPageRow.document_id == document_id)
        .order_by(DocumentPageRow.page_number)
    )
]
```

Return inside:

```python
DocumentStructure(
    document_id=document_id,
    source_file=source_file,
    pages=pages,
    sections=sections,
    blocks=blocks,
    source_chunks=chunks,
    assets=assets,
)
```

## Add `get_page()`

```python
def get_page(self, document_id: str, page_number: int) -> DocumentPage | None:
    row = self.session.scalars(
        select(DocumentPageRow).where(
            DocumentPageRow.document_id == document_id,
            DocumentPageRow.page_number == page_number,
        )
    ).first()
    return self._page_model(row) if row else None
```

## Migration

Create migration:

```text
add_document_pages
```

It should:

```text
[ ] create document_pages
[ ] add index on document_id
[ ] add index/unique constraint on document_id + page_number
[ ] optionally backfill from parsed_documents.pages
```

## Tests

```text
[ ] Save structure with pages.
[ ] Load structure and verify page order.
[ ] Get page by number.
[ ] Missing page returns None.
[ ] Re-saving replaces old pages.
```

## Acceptance Criteria

```text
[ ] `DocumentPage` is a first-class persisted rich structure entity.
[ ] Page persistence no longer depends on `parsed_documents`.
```
