# 09 — Phase 6: Remove Old Local Navigation Layer

## Goal

Remove duplicate local navigation code and storage after rich structure navigation is working.

## Stop Writing Old Data

New ingestion should not write:

```text
parsed_documents
navigation_indexes
```

## Files to Inspect

```text
app/services/indexing_service.py
app/indexing/parsers.py
app/indexing/navigation_index_builder.py
app/storage/repositories/documents.py
app/storage/tables.py
tests/...
```

## Remove Runtime Fallbacks

Do not keep permanent fallback logic like:

```python
if rich_structure:
    use_rich()
else:
    use_old_parsed_navigation()
```

Temporary migration scripts are okay.

Permanent runtime fallback is not.

## Remove Tables

After migration/backfill and tests:

```text
drop parsed_documents
drop navigation_indexes
```

## Remove Code Candidates

```text
app/indexing/parsers.py
app/indexing/navigation_index_builder.py
app/retrieval/navigation_engine.py
app/integrations/pageindex_adapter.py
DocumentRepository.save_parsed()
DocumentRepository.get_parsed()
DocumentRepository.save_navigation_index()
DocumentRepository.get_navigation_index()
ParsedDocumentRow
NavigationIndexRow
```

## Search Before Deleting

Run:

```bash
rg "get_parsed|save_parsed|ParsedDocumentRow|NavigationIndexRow|get_navigation_index|save_navigation_index|PageIndexAdapter|NavigationRetrievalEngine|NavigationIndexBuilder"
```

Every match should be removed, migrated, or clearly justified.

## Acceptance Criteria

```text
[ ] New ingestion does not write `parsed_documents`.
[ ] New ingestion does not write `navigation_indexes`.
[ ] Query APIs do not depend on old tables.
[ ] Page APIs do not depend on old tables.
[ ] Structure APIs do not depend on old tables.
[ ] Old code is deleted or fully unreachable.
[ ] Old tables are dropped after safe migration.
```
