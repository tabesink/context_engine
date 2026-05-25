# 07 — Phase: Remove Old Navigation Stack

## Goal

Delete duplicate local navigation code after the rich path is wired and tested.

## Old Tables to Remove

```text
parsed_documents
navigation_indexes
```

Only drop after migration/backfill.

## Old Code Candidates

```text
app/indexing/parsers.py
app/indexing/navigation_index_builder.py
app/retrieval/navigation_engine.py
app/integrations/pageindex_adapter.py
app/services/indexing_service.py
```

## Old Repository Methods

Remove from document repository:

```text
save_parsed()
get_parsed()
save_navigation_index()
get_navigation_index()
```

## Old Domain Models

Remove old parsed document concepts if no longer used:

```text
Page
ParsedDocument
```

Keep rich names:

```text
DocumentPage
DocumentStructure
SourceChunk
Evidence
PageRef
SectionRef
```

## Grep Checklist

Run:

```bash
rg "get_parsed|save_parsed|ParsedDocumentRow|NavigationIndexRow|get_navigation_index|save_navigation_index|PageIndexAdapter|NavigationRetrievalEngine|NavigationIndexBuilder|IndexingService"
```

Every match should be:

```text
removed
migrated
or only present in historical migration comments
```

## Migration

After verification:

```text
drop parsed_documents
drop navigation_indexes
```

## Acceptance Criteria

```text
[ ] No runtime references to old local navigation stack.
[ ] Old tables are dropped after safe migration.
[ ] Old services/adapters/builders are deleted.
[ ] Tests use rich structure only.
```
