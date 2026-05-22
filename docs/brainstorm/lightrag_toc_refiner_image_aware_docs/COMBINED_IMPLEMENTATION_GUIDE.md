# Combined Implementation Guide: Docling + PageIndex TOC Refiner + LightRAG Image-Aware Retrieval


---

<!-- 01_architecture_decision_record.md -->

# 01 — Architecture Decision Record

## Decision

Use a single canonical document-structure pipeline that combines the strengths of Docling, PageIndex, and LightRAG without duplicating responsibilities.

```text
Original document
  -> Docling parse
  -> DocumentStructure manifest
  -> extracted assets saved to storage
  -> structure quality scoring
  -> optional PageIndex-style LLM TOC refinement
  -> final sections / blocks / chunks
  -> LightRAG ingestion with metadata references
  -> query result
  -> Context Engine resolves sources + images
```

## Why This Design

The system has three different responsibilities:

| Responsibility | Owner | Reason |
|---|---|---|
| Structure-aware parsing | Docling + Context Engine | Deterministic parsing, layout, blocks, pages, tables, figures, images |
| TOC/page-range recovery | PageIndex-style refiner | LLM-based TOC reasoning is useful when PDFs have messy or offset TOCs |
| Semantic and graph retrieval | LightRAG | Avoid duplicate embedding/vector/KG storage |

## What This Avoids

This design avoids:

```text
- two independent document navigation systems
- duplicate semantic chunks in Postgres
- duplicate embeddings outside LightRAG
- image bytes inside LightRAG
- PageIndex workspace persistence beside Context Engine persistence
- LLM-first parsing for every document
- heavy multimodal retrieval infrastructure in v1
```

## Final Ownership Boundary

### Context Engine Owns

```text
uploaded document metadata
original file location
document structure manifest
sections
blocks
chunks
tables/figures/images metadata
extracted asset files
asset thumbnails
page/section/chunk lookup
TUI/API debugging views
ingestion job state
LightRAG domain/document association
```

### LightRAG Owns

```text
semantic chunks
embeddings
vector index
entity extraction
relationship extraction
knowledge graph retrieval
LightRAG domain-local retrieval state
```

## Important Architectural Rule

LightRAG may receive metadata like this:

```json
{
  "document_id": "doc_123",
  "section_id": "sec_004",
  "chunk_id": "chunk_004_002",
  "page_start": 12,
  "page_end": 14,
  "asset_ids": ["asset_018"]
}
```

LightRAG must not receive:

```text
- image bytes
- base64 images
- full document manifests
- duplicate local database state
- binary asset files
```

## Final Recommendation

Use this shape:

```text
Docling = parser of record
PageIndex TOC logic = optional refiner
Context Engine = navigation + assets + orchestration
LightRAG = semantic retrieval + KG retrieval
```

---

<!-- 02_user_capabilities.md -->

# 02 — User Capabilities

This system is stronger than normal RAG because it supports semantic retrieval plus document navigation plus image-aware source evidence.

## A User Can Ask Normal RAG Questions

```text
What does the manual say about hydraulic pressure limits?
How do I reset the controller?
What are the installation requirements?
Which documents discuss calibration?
```

## A User Can Ask Navigation-Aware Questions

```text
Where in the document is the maintenance schedule?
Which page discusses alarm code E42?
Show me the subsection under Preventive Maintenance that talks about filters.
What are the child sections under Installation?
Give me the content from pages 14 to 17.
```

The answer should include:

```text
document name
section path
page range
chunk/source ids
answer text
related images/tables/figures when relevant
```

## A User Can Ask Structure-Based Summary Questions

```text
Summarize Chapter 3.
Summarize every subsection under Operation.
Create a one-page summary of this manual.
What are the main procedures in this document?
```

## A User Can Ask Procedure Extraction Questions

```text
Give me the step-by-step startup procedure.
Extract the shutdown procedure.
Create a checklist from the maintenance section.
What warnings apply before performing this repair?
```

## A User Can Ask Image/Figure/Table Questions

```text
Which figure shows the wiring diagram?
Show me the image related to the controller harness.
Which table lists torque specifications?
What diagram explains the hydraulic circuit?
Find all figures related to the maintenance procedure.
```

The system should return the answer and related assets:

```json
{
  "answer": "The wiring diagram shows the controller connected to the emergency stop circuit and sensor harness.",
  "sources": [
    {
      "document_id": "doc_123",
      "section_title": "Electrical Wiring",
      "page_start": 18,
      "page_end": 20,
      "chunk_id": "chunk_007_002"
    }
  ],
  "assets": [
    {
      "asset_id": "asset_044",
      "type": "figure",
      "caption": "Figure 6. Main controller wiring diagram",
      "thumbnail_url": "/api/documents/doc_123/assets/asset_044/thumbnail",
      "url": "/api/documents/doc_123/assets/asset_044"
    }
  ]
}
```

## Admin / Debug Questions

```text
Did Docling detect the table of contents correctly?
Did the PageIndex-style TOC refiner run?
Which chunks were sent to LightRAG?
Which assets are linked to this chunk?
Which section/page did this answer come from?
Why was this image returned?
Which documents failed structure validation?
```

## The Main Value Proposition

Normal RAG answers:

```text
What does the document say?
```

This system answers:

```text
What does the document say?
Where does it say it?
What section/page/chunk supports it?
What diagram/table/image is associated with it?
How can I navigate the original document?
```

---

<!-- 03_canonical_models.md -->

# 03 — Canonical Models

Use one canonical internal representation for document structure. Do not let Docling, PageIndex, and LightRAG each create their own competing structure model.

## Core Models

```python
from pydantic import BaseModel
from typing import Literal

class DocumentStructure(BaseModel):
    document_id: str
    source_file: str
    parser: Literal["docling"] = "docling"
    parser_version: str | None = None
    pages: list["DocumentPage"] = []
    sections: list["DocumentSection"] = []
    blocks: list["DocumentBlock"] = []
    chunks: list["DocumentChunk"] = []
    assets: list["DocumentAsset"] = []
    quality: "StructureQuality" | None = None
    warnings: list[str] = []
```

## Page Model

```python
class DocumentPage(BaseModel):
    page_number: int
    width: float | None = None
    height: float | None = None
    text: str | None = None
```

## Section Model

```python
class DocumentSection(BaseModel):
    section_id: str
    document_id: str
    title: str
    level: int
    parent_section_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    block_ids: list[str] = []
    child_section_ids: list[str] = []
    summary: str | None = None
    source: Literal["docling", "toc_refiner", "fallback"] = "docling"
    confidence: float | None = None
```

## Block Model

```python
class DocumentBlock(BaseModel):
    block_id: str
    document_id: str
    section_id: str | None = None
    type: Literal[
        "heading",
        "paragraph",
        "table",
        "figure",
        "caption",
        "image",
        "code",
        "list",
        "page_header",
        "page_footer",
        "unknown",
    ]
    text: str = ""
    page_start: int | None = None
    page_end: int | None = None
    bbox: dict | None = None
    reading_order: int | None = None
    asset_ids: list[str] = []
```

## Asset Model

Images detected by Docling are first-class assets.

```python
class DocumentAsset(BaseModel):
    asset_id: str
    document_id: str
    asset_type: Literal["image", "figure", "table_image", "page_snapshot"]
    storage_path: str
    thumbnail_path: str | None = None
    mime_type: str = "image/png"
    content_hash: str

    page_number: int | None = None
    section_id: str | None = None
    block_id: str | None = None
    chunk_id: str | None = None

    caption: str | None = None
    nearby_text: str | None = None
    bbox: dict | None = None

    generated_description: str | None = None
    ocr_text: str | None = None
```

## Chunk Model

```python
class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    section_id: str | None = None
    block_ids: list[str]
    text: str
    page_start: int | None = None
    page_end: int | None = None
    asset_ids: list[str] = []
    metadata: dict = {}
```

## Structure Quality Model

This decides whether to run the PageIndex-style LLM TOC refiner.

```python
class StructureQuality(BaseModel):
    heading_count: int = 0
    section_count: int = 0
    block_count: int = 0
    asset_count: int = 0
    has_toc: bool = False
    has_page_ranges: bool = False
    has_deep_hierarchy: bool = False
    unsectioned_block_ratio: float = 0.0
    invalid_page_range_count: int = 0
    score: float = 0.0
    should_run_toc_refiner: bool = False
    reasons: list[str] = []
```

## Model Rule

The final `DocumentStructure` is the only structure the rest of the system uses.

```text
Docling output -> converted into DocumentStructure
PageIndex-style output -> merged into DocumentStructure
LightRAG metadata -> references DocumentStructure ids
API/TUI -> reads DocumentStructure ids
```

---

<!-- 04_ingestion_pipeline.md -->

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

---

<!-- 05_pageindex_toc_llm_refiner.md -->

# 05 — PageIndex-Style LLM TOC Refiner

## Main Point

PageIndex's LLM-based TOC indexing is valuable and should be preserved as a design idea.

It is better than Docling for one specific job:

```text
Recovering a usable section tree and physical page ranges from messy PDF tables of contents.
```

It is not better as the whole parser.

## Why This Matters

Many manuals have a visible TOC, but the PDF's physical page numbers do not match the printed page numbers.

Example:

```text
Printed manual page 1 may be PDF physical page 9.
TOC says "Installation ........ 12".
Actual PDF page may be 20.
```

PageIndex-style logic is useful because it tries to solve:

```text
TOC page detection
TOC extraction
TOC to JSON conversion
logical page number -> physical PDF page mapping
page offset calculation
section start validation
missing page repair
fallback hierarchy generation
```

## Correct Role in This System

Use PageIndex logic as a conditional refinement pass.

```text
Docling parses everything first.
Then structure quality is scored.
If structure is weak or TOC recovery would help, run the TOC refiner.
The refiner returns section improvements.
The final output is still the canonical DocumentStructure.
```

## Do Not Run It for Every Document

LLM TOC indexing costs tokens, time, and introduces variability.

Run it only when:

```text
Docling produced too few sections
Docling found blocks but weak headings
TOC pages are likely present
section page ranges are missing
page ranges are invalid
admin explicitly requests rebuild with LLM TOC refinement
```

Skip it when:

```text
Markdown headings are reliable
Docling produced good section hierarchy
document is small
page ranges are valid
asset/block links are already good
```

## Refiner Interface

```python
class TocRefiner:
    async def refine(
        self,
        pages: list[DocumentPage],
        blocks: list[DocumentBlock],
        initial_sections: list[DocumentSection],
        options: "TocRefinerOptions",
    ) -> "TocRefinementResult":
        ...
```

```python
class TocRefinerOptions(BaseModel):
    enabled: bool = False
    max_llm_calls: int = 8
    model: str
    temperature: float = 0.0
    toc_scan_page_limit: int = 20
    validate_sample_count: int = 12
    min_acceptance_accuracy: float = 0.70
    allow_fallback_tree_generation: bool = True
```

```python
class TocRefinementResult(BaseModel):
    accepted: bool
    reason: str
    toc_pages: list[int] = []
    logical_to_physical_offset: int | None = None
    sections: list[DocumentSection] = []
    validation_accuracy: float | None = None
    warnings: list[str] = []
    llm_call_count: int = 0
```

## Refiner Algorithm

```text
1. Scan first N pages for TOC-like pages.
2. Extract TOC text.
3. Detect whether the TOC contains page numbers.
4. Convert the TOC text into flat section rows:
   - title
   - level or structure number
   - printed page number if present
5. If printed page numbers exist:
   - sample early content pages
   - find where known TOC titles start physically
   - calculate most common page offset
   - assign physical page_start
6. If printed page numbers do not exist:
   - use LLM to locate section starts in tagged page text
7. Validate section starts by checking whether title appears near that page.
8. Repair invalid rows with bounded retry.
9. Calculate page_end from next section start.
10. Return refined sections only if acceptance threshold is met.
```

## Prompt Discipline

All prompts must return JSON only.

Bad:

```text
Tell me what you think about this TOC.
```

Good:

```text
Return only JSON matching this schema:
[
  {
    "title": "string",
    "level": 1,
    "printed_page": 12
  }
]
```

## Acceptance Policy

Do not blindly trust LLM output.

Accept the result only if:

```text
sections are non-empty
section page_start values are in bounds
section hierarchy is valid enough
validation accuracy >= min_acceptance_accuracy
LLM call count <= max_llm_calls
```

If not accepted:

```text
return initial Docling structure
add warning
continue ingestion
```

## Merge Policy

The TOC refiner may override:

```text
section title
section level
section parent/child relationships
section page_start
section page_end
block-to-section mapping
```

The TOC refiner must not override:

```text
asset files
asset ids
image paths
table extraction
figure extraction
Docling block text
original file metadata
LightRAG chunk ids once ingestion is complete
```

## Section Range Calculation

Given sorted section starts:

```python
def assign_section_ends(sections: list[DocumentSection], page_count: int) -> list[DocumentSection]:
    ordered = sorted(sections, key=lambda s: (s.page_start or 10**9, s.level))
    for i, section in enumerate(ordered):
        next_start = None
        for nxt in ordered[i + 1:]:
            if nxt.page_start and nxt.page_start >= (section.page_start or 1):
                next_start = nxt.page_start
                break
        section.page_end = (next_start - 1) if next_start else page_count
    return ordered
```

## Lightweight Implementation Modules

```text
app/document_processing/refinement/
  toc_page_detector.py
  toc_json_extractor.py
  page_offset_resolver.py
  section_start_validator.py
  section_range_assigner.py
  toc_refiner.py
```

## What to Keep from PageIndex

Keep these concepts:

```text
TOC page detection
TOC-to-JSON transformation
page number detection
logical page to physical page offset correction
section start validation
missing page-number repair
fallback hierarchy generation
large-section recursive splitting
accuracy checks before accepting LLM structure
```

## What Not to Copy from PageIndex Wholesale

Avoid:

```text
separate PageIndex workspace
separate document registry
full parallel retrieval API
unbounded prompt chains
LLM-first parsing for every document
PyPDF2 as parser of record
image/table handling through PageIndex
second structure format
```

## Final Rule

PageIndex-style TOC indexing is a useful refinement tool.

It should be implemented as:

```text
small bounded optional service
```

not as:

```text
second document navigation platform
```

---

<!-- 06_docling_asset_extraction.md -->

# 06 — Docling Asset Extraction

## Goal

Images, figures, and table snapshots detected by Docling must be saved and returned to users when associated chunks are retrieved.

## Asset Principle

Store images once. Pass references everywhere else.

```text
Good:
chunk.asset_ids = ["asset_044"]

Bad:
chunk.metadata.image_base64 = "..."
```

## File Layout

```text
.data/
  documents/
    {document_id}/
      original/
        source.pdf
      manifest/
        document_structure.json
      assets/
        asset_001.png
        asset_001_thumb.png
        asset_002.png
        asset_002_thumb.png
```

## Asset Extraction Steps

```text
1. Docling detects figure/image/table region.
2. Extract or render image to PNG/JPEG.
3. Compute content hash.
4. Save full-resolution asset.
5. Generate thumbnail.
6. Create DocumentAsset metadata.
7. Link asset to block/page/section.
8. Later link asset to chunk.
```

## Link Rules

Use simple deterministic rules first.

```text
1. If image has a caption block, link image to caption block.
2. If image block exists, link image to that block.
3. If no caption exists, link to nearest text block on same page.
4. Link to containing section by page range.
5. During chunking, chunk inherits asset_ids from included blocks.
```

## Caption Handling

Prefer human-authored captions.

```text
Figure 4. Hydraulic circuit diagram
Table 2. Torque specifications
```

If no caption exists, leave `caption = null` in v1.

Optional v2:

```text
run vision captioning only for uncaptained images
store generated_description
inject generated_description into chunk text if useful
```

## No Image Embeddings in v1

Do not add:

```text
CLIP embeddings
image vector search
separate image retriever
vision model processing for every asset
MinIO/S3 unless deployment requires it
```

The v1 image retrieval rule is enough:

```text
retrieved chunk -> asset_ids -> return image URLs/thumbnails
```

## Asset Deduplication

Use content hash.

```python
def compute_asset_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

If the same asset appears twice, store one file but allow multiple metadata links if needed.

## Thumbnail Rule

Generate thumbnails on ingestion.

```text
max width: 512 px
preserve aspect ratio
same file stem + _thumb suffix
```

The query response should return thumbnail URLs by default. The frontend/TUI can open the full asset when requested.

---

<!-- 07_lightrag_adapter_boundary.md -->

# 07 — LightRAG Adapter Boundary

## Goal

Keep LightRAG as the semantic retrieval engine without letting it own local navigation and asset storage.

## Adapter Responsibility

```python
class LightRagIngestionAdapter:
    async def ingest_chunks(
        self,
        domain_id: str,
        chunks: list[DocumentChunk],
    ) -> None:
        ...
```

```python
class LightRagQueryAdapter:
    async def query(
        self,
        domain_id: str,
        query: str,
        options: QueryOptions,
    ) -> LightRagQueryResult:
        ...
```

## Chunk Payload to LightRAG

```json
{
  "text": "Section: 4.2 Filter Replacement\nPage: 38-41\n...",
  "metadata": {
    "document_id": "doc_123",
    "section_id": "sec_004",
    "chunk_id": "chunk_004_002",
    "page_start": 38,
    "page_end": 41,
    "asset_ids": ["asset_018"]
  }
}
```

## What LightRAG Should Return

Ideally LightRAG returns:

```json
{
  "answer": "...",
  "sources": [
    {
      "chunk_id": "chunk_004_002",
      "document_id": "doc_123",
      "section_id": "sec_004",
      "score": 0.91
    }
  ]
}
```

If LightRAG cannot return all metadata directly, Context Engine should still maintain a mapping from uploaded text/chunk ids to local chunk records.

## Hard Boundary

LightRAG does not own:

```text
original uploaded files
extracted images
thumbnails
asset metadata tables
Docling manifests
PageIndex refinement logs
TUI navigation screens
Context Engine user permissions
```

## Why This Matters

This keeps the system simple:

```text
Context Engine is the control plane.
LightRAG is the retrieval engine.
```

No duplicate embeddings. No duplicate image storage. No parallel document navigation database.

---

<!-- 08_retrieval_with_images.md -->

# 08 — Retrieval With Images

## Query Flow

```text
User query
  -> Context Engine receives query
  -> Context Engine calls LightRAG domain query
  -> LightRAG returns answer + source chunk metadata
  -> Context Engine loads local chunk records
  -> Context Engine resolves section/page/source info
  -> Context Engine resolves asset_ids
  -> Context Engine returns answer + sources + images
```

## Response Shape

```json
{
  "answer": "The controller wiring diagram shows the emergency stop circuit and sensor harness connections.",
  "sources": [
    {
      "document_id": "doc_123",
      "document_name": "Service Manual.pdf",
      "section_id": "sec_007",
      "section_title": "Electrical Wiring",
      "page_start": 18,
      "page_end": 20,
      "chunk_id": "chunk_007_002"
    }
  ],
  "assets": [
    {
      "asset_id": "asset_044",
      "asset_type": "figure",
      "caption": "Figure 6. Main controller wiring diagram",
      "page_number": 19,
      "thumbnail_url": "/api/documents/doc_123/assets/asset_044/thumbnail",
      "url": "/api/documents/doc_123/assets/asset_044"
    }
  ]
}
```

## Asset Resolver

```python
def resolve_assets_for_retrieved_chunks(
    chunks: list[DocumentChunk],
    max_assets: int = 5,
) -> list[DocumentAsset]:
    asset_ids: list[str] = []
    for chunk in chunks:
        for asset_id in chunk.asset_ids:
            if asset_id not in asset_ids:
                asset_ids.append(asset_id)
    return asset_repo.get_many(asset_ids[:max_assets])
```

## Ranking Assets

When there are too many assets, rank simply:

```text
1. asset directly linked to retrieved chunk
2. asset linked to a block inside retrieved chunk
3. asset caption overlaps user query
4. asset is on same page as retrieved chunk
5. asset is in same section
6. asset is near retrieved page range
```

## Defaults

```text
include_assets: true
include_thumbnails: true
max_assets: 5
return_full_image_bytes: false
```

Return URLs, not bytes, in JSON responses.

## Frontend/TUI Behavior

In a full frontend:

```text
show answer
show source sections/pages
show image thumbnails inline
allow click to open full image
```

In TUI:

```text
show asset metadata
show thumbnail URL / file path
optionally open image externally if supported
```

## No Multimodal Retrieval in v1

Do not search directly over images in v1.

Retrieval path is:

```text
text query -> text chunk -> linked image
```

This is lightweight and predictable.

---

<!-- 09_api_contracts.md -->

# 09 — API Contracts

Keep APIs small and explicit.

## Upload

```http
POST /documents/upload
```

Request:

```json
{
  "domain_id": "manuals",
  "target_engine": "lightrag",
  "enable_toc_refinement": "auto"
}
```

Allowed `enable_toc_refinement` values:

```text
auto
always
never
```

## Query

```http
POST /domains/{domain_id}/query
```

Request:

```json
{
  "query": "Show me the wiring diagram for the controller.",
  "include_assets": true,
  "include_thumbnails": true,
  "max_assets": 5
}
```

Response:

```json
{
  "answer": "...",
  "sources": [],
  "assets": []
}
```

## Document Structure

```http
GET /documents/{document_id}/structure
```

Returns section tree without full block text by default.

Optional:

```http
GET /documents/{document_id}/structure?include_blocks=true&include_assets=true
```

## Section Detail

```http
GET /documents/{document_id}/sections/{section_id}
```

Returns:

```text
section metadata
page range
child sections
linked chunks
linked assets
```

## Chunk Detail

```http
GET /documents/{document_id}/chunks/{chunk_id}
```

Returns:

```text
chunk text
page range
section path
block ids
asset ids
LightRAG ingestion metadata
```

## Asset APIs

```http
GET /documents/{document_id}/assets/{asset_id}
GET /documents/{document_id}/assets/{asset_id}/thumbnail
```

These should stream files from local storage.

## Debug APIs

```http
GET /documents/{document_id}/ingestion-status
GET /documents/{document_id}/structure-quality
GET /documents/{document_id}/toc-refinement-report
GET /documents/{document_id}/chunks
GET /documents/{document_id}/assets
```

## Admin-only Actions

```http
POST /documents/{document_id}/rebuild-structure
POST /documents/{document_id}/reingest-lightrag
DELETE /documents/{document_id}
```

`rebuild-structure` request:

```json
{
  "enable_toc_refinement": "always",
  "preserve_assets": true
}
```

---

<!-- 10_storage_database_filesystem.md -->

# 10 — Storage, Database, and Filesystem

## Storage Rule

Use Postgres for metadata. Use filesystem for files.

Do not store image bytes in Postgres.

## Filesystem Layout

```text
.data/
  documents/
    {document_id}/
      original/
        source.pdf
      manifest/
        document_structure.json
        docling_raw.json
        toc_refinement_report.json
      assets/
        asset_001.png
        asset_001_thumb.png
        asset_002.png
        asset_002_thumb.png
```

## Tables

### documents

```text
id
filename
storage_path
domain_id
status
created_by
created_at
updated_at
```

### document_sections

```text
id
document_id
parent_section_id
title
level
page_start
page_end
source
confidence
```

### document_blocks

```text
id
document_id
section_id
type
text
page_start
page_end
bbox_json
reading_order
```

### document_chunks

```text
id
document_id
section_id
text
page_start
page_end
lightrag_status
lightrag_external_id
metadata_json
```

### document_assets

```text
id
document_id
section_id
block_id
chunk_id
asset_type
storage_path
thumbnail_path
mime_type
content_hash
page_number
caption
nearby_text
bbox_json
generated_description
ocr_text
```

### ingestion_jobs

```text
id
document_id
domain_id
status
stage
error_message
started_at
completed_at
metadata_json
```

### toc_refinement_reports

```text
id
document_id
enabled
accepted
reason
validation_accuracy
logical_to_physical_offset
llm_call_count
warnings_json
created_at
```

## JSON Manifest

Even with DB tables, save a manifest for debugging/reproducibility.

```text
.data/documents/{document_id}/manifest/document_structure.json
```

This makes it easy to inspect ingestion output outside the database.

## Deletion Policy

Soft delete first:

```text
documents.status = deleted
```

Physical deletion should require explicit admin action:

```text
--delete-permanently
```

Permanent delete removes:

```text
original file
manifest files
asset files
DB metadata
LightRAG domain document data if supported
```

---

<!-- 11_tui_debug_screens.md -->

# 11 — TUI Debug Screens

The TUI is for backend/API debugging, not a final user-facing app. Keep it monochrome, compact, and information-rich.

## Main Screens

```text
Dashboard
Domains
Documents
Document Detail
Structure Tree
Chunks
Assets
TOC Refinement Report
Query Tester
Retrieved Sources
Graph
Jobs
```

## Document Detail Screen

Show:

```text
document id
filename
domain
status
page count
section count
block count
chunk count
asset count
ingestion stage
LightRAG status
```

## Structure Quality Screen

Show:

```text
heading_count
section_count
asset_count
has_toc
has_page_ranges
unsectioned_block_ratio
invalid_page_range_count
score
should_run_toc_refiner
reasons
```

## TOC Refinement Report Screen

Show:

```text
enabled / disabled
reason it ran
TOC pages detected
LLM call count
accepted / rejected
validation accuracy
logical-to-physical page offset
warnings
```

Example:

```text
+------------------------------------------------------------+
| TOC Refinement                                             |
+--------------------------+---------------------------------+
| Enabled                  | auto                            |
| Ran                      | yes                             |
| Reason                   | Docling section_count < 3       |
| TOC pages                | 3, 4                            |
| Offset                   | +8                              |
| Validation accuracy      | 0.83                            |
| Accepted                 | yes                             |
| LLM calls                | 6 / 8                           |
+--------------------------+---------------------------------+
```

## Assets Screen

Show:

```text
asset_id
type
page
section
block
chunk
caption
thumbnail_path
```

## Query Tester Screen

When testing a query, show:

```text
answer
source chunks
section path
page range
asset ids
thumbnail URLs
LightRAG raw metadata if debug mode enabled
```

## Minimal UI Rule

Do not show everything by default. Use expandable views:

```text
[summary]
[structure]
[chunks]
[assets]
[raw json]
```

---

<!-- 12_testing_strategy.md -->

# 12 — Testing Strategy

## Unit Tests

### Structure Quality

Test:

```text
good Docling structure does not trigger refiner
flat structure triggers refiner
invalid page ranges trigger refiner
TOC detected triggers refiner
```

### TOC Refiner

Use fixtures with mocked LLM responses.

Test:

```text
TOC with printed page numbers
TOC without page numbers
PDF physical page offset
invalid LLM JSON
out-of-bounds page numbers
low validation accuracy rejection
bounded max_llm_calls
```

### Asset Extraction

Test:

```text
assets saved to expected path
thumbnails created
content hash calculated
duplicate assets detected
assets linked to blocks
assets inherited by chunks
```

### Chunk Builder

Test:

```text
chunks stay inside section boundaries when possible
chunk inherits asset_ids from blocks
chunk metadata includes page range
large sections split correctly
```

### Retrieval Asset Resolver

Test:

```text
retrieved chunks resolve assets
max_assets limit enforced
duplicate assets removed
caption-overlap ranking works
```

## Integration Tests

### Ingestion Without TOC Refiner

```text
upload document
Docling parse succeeds
structure score good
TOC refiner skipped
chunks sent to LightRAG
assets saved
```

### Ingestion With TOC Refiner

```text
upload messy manual
Docling parse succeeds but weak structure
TOC refiner runs
refined sections accepted
chunks sent to LightRAG with asset_ids
```

### Query With Images

```text
query mentions diagram
LightRAG returns relevant chunk
Context Engine resolves asset_ids
response includes thumbnail and full asset URL
```

## Golden Fixture Types

Keep a small test corpus:

```text
1. Clean Markdown document
2. PDF with reliable headings
3. PDF with TOC and page offset
4. PDF with weak headings but good TOC
5. PDF with figures and captions
6. PDF with tables
7. PDF with images but no captions
```

## Non-goals for v1 Tests

Do not test:

```text
CLIP embeddings
image semantic search
full multimodal answer generation
S3/MinIO storage
browser rendering
```

---

<!-- 13_incremental_implementation_plan.md -->

# 13 — Incremental Implementation Plan

## Phase 1 — Canonical Models

Implement:

```text
DocumentStructure
DocumentPage
DocumentSection
DocumentBlock
DocumentAsset
DocumentChunk
StructureQuality
```

Add tests for model validation and JSON serialization.

## Phase 2 — Docling Parser Adapter

Implement:

```text
DoclingParser
DocumentStructureBuilder
AssetExtractor
ThumbnailGenerator
```

Output:

```text
document_structure.json
asset files
asset metadata rows
```

## Phase 3 — Structure Quality Scoring

Implement:

```text
StructureQualityScorer
should_run_toc_refiner
```

No LLM yet.

## Phase 4 — PageIndex-Style TOC Refiner

Implement small bounded services:

```text
TocPageDetector
TocJsonExtractor
PageOffsetResolver
SectionStartValidator
SectionRangeAssigner
TocRefiner
```

Use mocked LLM tests first.

## Phase 5 — Merge Refiner Output

Implement:

```text
StructureMerger
BlockSectionAssigner
AssetSectionAssigner
```

Goal:

```text
refined sections + original Docling blocks/assets = final DocumentStructure
```

## Phase 6 — Chunk Builder

Implement:

```text
StructureAwareChunkBuilder
```

Chunks must include:

```text
chunk_id
document_id
section_id
block_ids
page range
asset_ids
text
```

## Phase 7 — LightRAG Adapter

Implement:

```text
LightRagIngestionAdapter
LightRagQueryAdapter
```

Send chunks with metadata only.

## Phase 8 — Retrieval Asset Resolver

Implement:

```text
RetrievedSourceResolver
RetrievedAssetResolver
```

Return:

```text
answer
sources
assets
```

## Phase 9 — APIs

Add:

```text
GET /documents/{document_id}/structure
GET /documents/{document_id}/assets/{asset_id}
GET /documents/{document_id}/assets/{asset_id}/thumbnail
GET /documents/{document_id}/toc-refinement-report
POST /domains/{domain_id}/query
```

## Phase 10 — TUI Debug Screens

Add screens for:

```text
structure quality
TOC refinement report
assets
chunks
query result with assets
```

## Recommended PR Order

```text
PR 1: models + storage paths
PR 2: Docling parser adapter + assets
PR 3: structure quality scorer
PR 4: TOC refiner with mocked LLM tests
PR 5: merger + chunk builder
PR 6: LightRAG adapter updates
PR 7: retrieval asset resolver
PR 8: API endpoints
PR 9: TUI debug screens
```

## Do Not Implement in v1

```text
image embeddings
image vector database
S3/MinIO
vision captioning for every image
local semantic fallback retrieval
duplicate embedding tables
large plugin framework
complex distributed storage
```

---

<!-- 14_coding_agent_prompt.md -->

# 14 — Coding Agent Prompt

Use this prompt with a coding agent.

```markdown
# Task: Implement Lightweight Docling + PageIndex TOC Refiner + LightRAG Document Navigation

You are a senior Python/FastAPI engineer. Write clean, lean, low-entropy code suitable for junior developers to maintain.

## Objective

Implement a document ingestion and retrieval pipeline where:

- Docling is the parser of record.
- Images/figures/tables detected by Docling are saved to Context Engine storage.
- PageIndex-style LLM TOC indexing is implemented as an optional bounded refinement layer.
- Context Engine owns document structure, assets, navigation, and debug APIs.
- LightRAG owns semantic retrieval, embeddings, and KG retrieval.
- Chunks sent to LightRAG include lightweight metadata and `asset_ids`, not image bytes.
- Retrieval responses include relevant image URLs/thumbnails when retrieved chunks have linked assets.

## Implementation Constraints

- Do not create a second document navigation system.
- Do not store image bytes in Postgres.
- Do not store image bytes or base64 in LightRAG.
- Do not implement local semantic fallback retrieval.
- Do not duplicate embeddings outside LightRAG.
- Do not create a large plugin framework.
- Keep modules explicit and small.
- Use Pydantic models or dataclasses.
- Use deterministic parsing first.
- Use LLM TOC refinement only when structure quality requires it.
- LLM calls must be bounded, logged, and validated.

## Required Modules

```text
app/document_processing/models.py
app/document_processing/docling_parser.py
app/document_processing/structure_builder.py
app/document_processing/asset_extractor.py
app/document_processing/thumbnail_generator.py
app/document_processing/structure_quality.py
app/document_processing/refinement/toc_refiner.py
app/document_processing/refinement/toc_page_detector.py
app/document_processing/refinement/page_offset_resolver.py
app/document_processing/refinement/section_start_validator.py
app/document_processing/structure_merger.py
app/document_processing/chunk_builder.py
app/services/lightrag_adapter.py
app/services/retrieval_asset_resolver.py
```

## Required APIs

```text
POST /documents/upload
GET /documents/{document_id}/structure
GET /documents/{document_id}/assets/{asset_id}
GET /documents/{document_id}/assets/{asset_id}/thumbnail
GET /documents/{document_id}/toc-refinement-report
POST /domains/{domain_id}/query
```

## Expected Ingestion Flow

```text
upload
  -> save original
  -> Docling parse
  -> save assets
  -> build initial DocumentStructure
  -> score structure quality
  -> run TOC refiner if needed
  -> merge refined sections with Docling blocks/assets
  -> build chunks
  -> send chunks to LightRAG with asset_ids
  -> save final manifest
```

## Expected Retrieval Flow

```text
query
  -> call LightRAG
  -> get source chunk ids
  -> load local chunks/sections/assets
  -> return answer + sources + related images
```

## Testing Requirements

Add tests for:

- model serialization
- asset extraction and thumbnail generation
- structure quality scoring
- TOC refiner trigger logic
- TOC refiner acceptance/rejection with mocked LLM output
- section range assignment
- chunk asset inheritance
- retrieval asset resolver
- query response includes assets

## Final Deliverable

Produce small, readable code with explicit boundaries. Prefer simple functions and classes over clever abstractions.
```

---

<!-- README.md -->

# Docling + PageIndex TOC Refiner + LightRAG: Lightweight Implementation Package

This package describes a lightweight document ingestion and retrieval architecture for `context_engine` and the custom LightRAG deployment.

## Final Architecture

```text
Docling parser of record
    -> canonical DocumentStructure
    -> image/table/figure asset extraction
    -> optional PageIndex-style LLM TOC refiner
    -> section/block/chunk mapping
    -> LightRAG text ingestion with asset references
    -> retrieval response with answer + sources + images
```

## Key Decisions

1. **Docling is the parser of record.**
2. **PageIndex-style LLM TOC indexing is valuable, but only as a conditional refiner.**
3. **Context Engine owns document structure, asset files, asset metadata, navigation, and debug APIs.**
4. **LightRAG owns semantic retrieval, embeddings, and KG retrieval.**
5. **Images detected by Docling are stored once in Context Engine storage.**
6. **Chunks sent to LightRAG include only lightweight `asset_ids`, not binary image data.**
7. **During retrieval, Context Engine resolves `asset_ids` and returns relevant image URLs/thumbnails to the user.**

## Recommended Reading Order

1. `01_architecture_decision_record.md`
2. `02_user_capabilities.md`
3. `03_canonical_models.md`
4. `04_ingestion_pipeline.md`
5. `05_pageindex_toc_llm_refiner.md`
6. `06_docling_asset_extraction.md`
7. `07_lightrag_adapter_boundary.md`
8. `08_retrieval_with_images.md`
9. `09_api_contracts.md`
10. `10_storage_database_filesystem.md`
11. `11_tui_debug_screens.md`
12. `12_testing_strategy.md`
13. `13_incremental_implementation_plan.md`
14. `14_coding_agent_prompt.md`

## Implementation Goal

Build a system that lets users ask:

```text
What does this manual say?
Where does it say it?
Which section/page/table/figure supports it?
Show me the related image or diagram.
Show me the retrieval path and source chunks.
```

The system should remain small, explicit, and junior-developer friendly.
