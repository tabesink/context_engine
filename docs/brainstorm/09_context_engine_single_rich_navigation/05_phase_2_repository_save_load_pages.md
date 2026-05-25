# 05 — Phase 2: Save and Load Pages in `DocumentProcessingRepository`

## Goal

Make `DocumentProcessingRepository.save_structure()` persist the full rich structure, including `pages`.

## Files to Change

```text
app/storage/repositories/document_processing.py
app/storage/tables.py
tests/storage/test_document_processing_repository.py
```

## Update Imports

```python
from app.document_processing.models import DocumentPage
from app.storage.tables import DocumentPageRow
```

## Update Delete Order in `save_structure()`

Pages should be deleted/replaced with the rest of the structure:

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

## Save Pages

```python
for page in structure.pages:
    self.session.add(self._page_row(structure.document_id, page))
```

## Load Pages in `get_structure()`

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

Then return:

```python
return DocumentStructure(
    document_id=document_id,
    source_file=source_file,
    pages=pages,
    sections=sections,
    blocks=blocks,
    source_chunks=chunks,
    assets=assets,
)
```

## Add Helpers

```python
def _page_row(self, document_id: str, page: DocumentPage) -> DocumentPageRow:
    return DocumentPageRow(
        id=f"{document_id}:page:{page.page_number}",
        document_id=document_id,
        page_number=page.page_number,
        width=page.width,
        height=page.height,
        text=page.text,
        meta=getattr(page, "metadata", {}) or {},
    )

def _page_model(self, row: DocumentPageRow) -> DocumentPage:
    return DocumentPage(
        page_number=row.page_number,
        width=row.width,
        height=row.height,
        text=row.text,
        metadata=row.meta or {},
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

## Tests

Add tests for:

```text
[ ] `save_structure()` persists pages.
[ ] `get_structure()` returns pages ordered by page number.
[ ] `get_page()` returns one page.
[ ] `get_page()` returns `None` for missing page.
[ ] Re-saving a structure replaces old pages.
```

## Acceptance Criteria

```text
[ ] `DocumentStructure.pages` survives save/load.
[ ] Page order is deterministic.
[ ] Existing structure APIs still work.
```
