# 08 — Phase 5: Implement `RichNavigationEngine`

## Goal

Replace the old page-only local navigation retrieval with deterministic search over the rich document structure.

## Files to Add or Change

```text
app/retrieval/rich_navigation_engine.py
app/services/retrieval_service.py
app/retrieval/strategies.py
tests/retrieval/test_rich_navigation_engine.py
```

## Responsibility

`RichNavigationEngine` should answer:

```text
Where in the document is this discussed?
Which section/page/chunk/table/image is relevant?
```

It should not perform local semantic retrieval.

It should not call an LLM.

## Search Sources and Weights

Recommended first version:

| Match Source | Weight |
|---|---:|
| Section title exact/partial match | 3.0 |
| Source chunk text match | 2.0 |
| Block text match | 1.5 |
| Page text match | 1.0 |
| Asset caption/nearby text match | 1.0 |

## Scoring Helper

```python
def tokenize(value: str) -> set[str]:
    return {
        token.lower().strip(".,:;!?()[]{}")
        for token in value.split()
        if len(token.strip()) > 2
    }

def overlap_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    text_terms = tokenize(text)
    return len(query_terms & text_terms) / len(query_terms)
```

## Evidence Output

Return `Evidence` objects with:

```text
source_engine = "navigation"
text = source chunk text, block text, or page text
page_ref = PageRef(document_id, page_start, page_end)
section_ref = SectionRef(document_id, section_id, title, page_start, page_end)
metadata = {
    "source": "source_chunk" | "section" | "block" | "page" | "asset",
    "chunk_id": "...",
    "section_id": "...",
    "block_ids": [...],
    "asset_ids": [...]
}
```

## Retrieval Algorithm

```text
RichNavigationEngine.retrieve(query, document_ids, top_k, user_id)
    │
    ├── choose target documents
    │     └── document_ids or readable ready documents
    │
    ├── load DocumentStructure for each document
    │
    ├── index by id:
    │     ├── sections_by_id
    │     ├── blocks_by_id
    │     ├── chunks_by_id
    │     └── assets_by_id
    │
    ├── score sections
    ├── score chunks
    ├── score blocks
    ├── score pages
    ├── score assets
    │
    ├── merge/dedupe by strongest citation unit
    │
    └── return top_k Evidence
```

## Dedupe Rule

Prefer more precise evidence:

```text
source_chunk > block > section > page > asset-only
```

## Wire Into Retrieval Service

Replace:

```python
from app.retrieval.navigation_engine import NavigationRetrievalEngine
```

with:

```python
from app.retrieval.rich_navigation_engine import RichNavigationEngine
```

Then:

```python
self.navigation_engine = RichNavigationEngine(session)
```

## Tests

```text
[ ] Query matches section title.
[ ] Query matches source chunk.
[ ] Query matches block.
[ ] Query matches page text.
[ ] Evidence includes page range.
[ ] Evidence includes section title when available.
[ ] Evidence metadata includes chunk/block/asset IDs.
[ ] Missing structure returns no evidence.
[ ] `top_k` is respected.
[ ] Hybrid retrieval still combines LightRAG and navigation evidence.
```

## Acceptance Criteria

```text
[ ] `mode=navigation` uses `RichNavigationEngine`.
[ ] No query-time call to `PageIndexAdapter`.
[ ] No query-time call to `DocumentRepository.get_parsed()`.
[ ] No query-time call to `DocumentRepository.get_navigation_index()`.
```
