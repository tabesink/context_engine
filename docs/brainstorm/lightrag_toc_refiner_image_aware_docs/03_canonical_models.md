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
