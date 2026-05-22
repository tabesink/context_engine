# 04 — Ingestion Pipeline

## Target Flow

```text
POST /documents/upload
    -> save original file
    -> create ingestion job
    -> run Docling parse
    -> save extracted assets
    -> build initial DocumentStructure
    -> score structure quality
    -> optionally run PageIndex-style TOC refiner
    -> merge refined TOC with Docling blocks/assets
    -> validate page ranges and asset links
    -> build chunks
    -> send chunks to LightRAG
    -> mark ingestion complete
```

## Step 1 — Save Original File

Store the original file under:

```text
.data/documents/{document_id}/original/{filename}
```

Create a DB row:

```text
documents.status = uploaded
```

## Step 2 — Run Docling

Docling is the parser of record.

Expected output:

```text
pages
text blocks
headings
tables
figures
images
captions
reading order
layout positions when available
```

## Step 3 — Save Assets

For every Docling-detected image/figure/table image:

```text
1. compute hash
2. save binary file
3. create thumbnail
4. create DocumentAsset
5. link asset to page/block/section when possible
```

## Step 4 — Build Initial DocumentStructure

Convert Docling output into:

```text
DocumentPage
DocumentBlock
DocumentSection
DocumentAsset
```

At this point the structure may be imperfect. That is acceptable.

## Step 5 — Score Structure Quality

Run deterministic checks:

```text
heading count
section count
TOC presence
page-range presence
unsectioned block ratio
invalid page ranges
asset link coverage
```

Example rule:

```python
def should_run_toc_refiner(q: StructureQuality) -> bool:
    return (
        q.has_toc
        or q.section_count < 3
        or not q.has_page_ranges
        or q.invalid_page_range_count > 0
        or q.unsectioned_block_ratio > 0.35
    )
```

## Step 6 — Optional PageIndex-Style TOC Refiner

Run only when structure quality is weak or a TOC likely exists.

The refiner should:

```text
detect TOC pages
extract TOC text
convert TOC to normalized section rows
map logical page numbers to physical pages
calculate page offset
validate section starts
repair missing or incorrect page ranges
return TocRefinementResult
```

## Step 7 — Merge Refined TOC with Docling Blocks/Assets

The TOC refiner should not produce a competing document store.

It should only improve:

```text
section titles
section hierarchy
section page_start/page_end
block-to-section assignment
chunk-to-section assignment
```

It must preserve:

```text
Docling blocks
Docling images
Docling tables
Docling captions
asset ids
source file paths
```

## Step 8 — Build Chunks

Chunks should be section-aware.

Rules:

```text
- prefer chunk boundaries inside section boundaries
- include section title/path in chunk text metadata
- inherit asset_ids from contained blocks
- preserve page_start/page_end
- keep chunk size bounded
```

## Step 9 — Send to LightRAG

Send text chunks with metadata only.

```json
{
  "text": "Section: Electrical Wiring\n...",
  "metadata": {
    "document_id": "doc_123",
    "section_id": "sec_007",
    "chunk_id": "chunk_007_002",
    "page_start": 18,
    "page_end": 20,
    "asset_ids": ["asset_044"]
  }
}
```

## Step 10 — Mark Complete

Only mark ingestion complete when:

```text
DocumentStructure saved
assets saved
chunks built
LightRAG ingestion accepted
```

If LLM TOC refinement fails, ingestion may still complete with warnings.
