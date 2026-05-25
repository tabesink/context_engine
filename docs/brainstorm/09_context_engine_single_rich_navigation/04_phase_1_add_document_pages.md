# 04 — Phase 1: Add `document_pages`

## Goal

Persist `DocumentPage` inside the rich document structure layer.

## Files to Change

```text
app/storage/tables.py
app/document_processing/models.py
alembic/versions/<revision>_add_document_pages.py
tests/storage/test_document_processing_repository.py
```

## Add `DocumentPageRow`

Add a SQLAlchemy row similar to:

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

Recommended ID:

```text
{document_id}:page:{page_number}
```

Recommended unique constraint:

```text
UNIQUE(document_id, page_number)
```

## Update `DocumentPage` Model

If needed, add page metadata:

```python
metadata: dict = Field(default_factory=dict)
```

## Migration Requirements

Create an Alembic migration that:

1. Creates `document_pages`.
2. Adds an index on `document_id`.
3. Adds an index or unique constraint on `(document_id, page_number)`.
4. Optionally backfills pages from `parsed_documents.pages`.

## Optional Backfill Strategy

```text
for each parsed_documents row:
    for each page in row.pages:
        insert document_pages:
            document_id = row.document_id
            page_number = page["number"]
            text = page["text"]
            metadata = page["metadata"]
```

## Acceptance Criteria

```text
[ ] `document_pages` table exists.
[ ] `DocumentPageRow` is mapped.
[ ] Migration works on a fresh DB.
[ ] Migration works on a DB with old parsed pages.
[ ] No API behavior changes yet.
```
