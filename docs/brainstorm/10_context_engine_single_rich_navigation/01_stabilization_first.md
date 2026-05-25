# 01 — Stabilization First

## Why This Must Come First

The updated repo is likely in a dangerous middle state:

```text
New rich navigation code exists,
but old runtime wiring still exists.
```

That means developers may incorrectly assume the new design is active when it is not.

## Stabilization Objective

Make the repo internally consistent before performing larger deletions.

## Required Stabilization Tasks

## Task 1 — Verify/Add `DocumentPageRow`

Search:

```bash
rg "DocumentPageRow|document_pages"
```

Expected final state:

```text
DocumentPageRow exists in app/storage/tables.py
document_pages migration exists
DocumentProcessingRepository imports DocumentPageRow successfully
```

Target table:

```text
document_pages
 ├── id
 ├── document_id
 ├── page_number
 ├── width
 ├── height
 ├── text
 └── metadata
```

## Task 2 — Verify/Add `DocumentPage.metadata`

Target model:

```python
class DocumentPage(BaseModel):
    page_number: int
    width: float | None = None
    height: float | None = None
    text: str | None = None
    metadata: dict = Field(default_factory=dict)
```

## Task 3 — Make `DocumentProcessingRepository` Page-Safe

Required methods:

```text
save_structure() saves pages
get_structure() loads pages
get_page(document_id, page_number) returns one rich page
```

## Task 4 — Add Tests Before Deleting Old Code

Minimum tests:

```text
tests/storage/test_document_processing_repository.py
  - save/load pages
  - get one page
  - missing page returns None
  - resave replaces pages
```

## Stabilization Acceptance Criteria

```text
[ ] App imports successfully.
[ ] Alembic migration creates `document_pages`.
[ ] Rich structure save/load includes pages.
[ ] Unit tests pass for page persistence.
[ ] No old code has been deleted yet.
```
