# 03 — Phase: Wire `RichNavigationEngine`

## Goal

Make query-time local navigation use rich `DocumentStructure`, not the old parsed/navigation index path.

## Files to Inspect/Change

```text
app/retrieval/rich_navigation_engine.py
app/retrieval/navigation_engine.py
app/retrieval/strategies.py
app/services/retrieval_service.py
app/integrations/pageindex_adapter.py
tests/retrieval/test_rich_navigation_engine.py
tests/api/test_query_navigation.py
```

## Current Anti-Pattern

```text
POST /query/retrieve
      │
      ▼
RetrievalService
      │
      ▼
NavigationRetrievalEngine
      │
      ├── parsed_documents
      └── navigation_indexes
```

## Target

```text
POST /query/retrieve
      │
      ▼
RetrievalService
      │
      ▼
RichNavigationEngine
      │
      ▼
DocumentProcessingRepository.get_structure()
      │
      ├── pages
      ├── sections
      ├── blocks
      ├── source_chunks
      └── assets
```

## Required Code Change

In `RetrievalService`, replace:

```python
from app.retrieval.navigation_engine import NavigationRetrievalEngine
```

with:

```python
from app.retrieval.rich_navigation_engine import RichNavigationEngine
```

Then replace:

```python
self.navigation_engine = NavigationRetrievalEngine(session)
```

with:

```python
self.navigation_engine = RichNavigationEngine(session)
```

## Strategy Type Cleanup

If `strategies.py` imports/types against `NavigationRetrievalEngine`, change it to accept a protocol or a generic object with `.retrieve()`.

Preferred:

```python
class NavigationEngineProtocol(Protocol):
    def retrieve(self, request: RetrievalRequest) -> list[Evidence]:
        ...
```

Do not make strategies depend on a concrete old class.

## Rich Navigation Rules

`RichNavigationEngine` should search deterministically:

```text
1. section titles
2. source chunks
3. blocks
4. pages
5. asset captions/nearby text
```

No LLM.

No embeddings.

No local semantic fallback.

## Evidence Output

Evidence should include:

```text
source_engine = "navigation"
text
score
page_start/page_end
section_title
metadata:
  source = section/source_chunk/block/page/asset
  section_id
  chunk_id
  block_ids
  asset_ids
```

## Tests

```text
[ ] mode=navigation returns rich evidence.
[ ] Evidence includes page_start/page_end.
[ ] Evidence includes section_title where available.
[ ] Evidence metadata contains rich IDs.
[ ] Missing rich structure returns empty evidence or controlled error.
[ ] mode=hybrid still merges LightRAG + rich navigation.
[ ] No query-time call to PageIndexAdapter.
[ ] No query-time call to DocumentRepository.get_parsed().
[ ] No query-time call to DocumentRepository.get_navigation_index().
```

## Acceptance Criteria

```text
[ ] `RichNavigationEngine` is live runtime code.
[ ] Old `NavigationRetrievalEngine` is no longer used by retrieval.
[ ] `PageIndexAdapter` is no longer used by retrieval.
```
