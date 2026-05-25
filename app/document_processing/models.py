from typing import Literal

from pydantic import BaseModel, Field


class DocumentPage(BaseModel):
    page_number: int
    width: float | None = None
    height: float | None = None
    text: str | None = None
    metadata: dict = Field(default_factory=dict)


class DocumentSection(BaseModel):
    section_id: str
    document_id: str
    title: str
    level: int
    parent_section_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    block_ids: list[str] = Field(default_factory=list)
    child_section_ids: list[str] = Field(default_factory=list)
    summary: str | None = None
    source: Literal["docling", "fallback"] = "docling"
    confidence: float | None = None


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
    asset_ids: list[str] = Field(default_factory=list)


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


class SourceChunk(BaseModel):
    """A citation/navigation unit; semantic ownership stays in LightRAG."""

    chunk_id: str
    document_id: str
    section_id: str | None = None
    block_ids: list[str]
    text: str
    page_start: int | None = None
    page_end: int | None = None
    asset_ids: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {"semantic_owner": "lightrag"})


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
    reasons: list[str] = Field(default_factory=list)


class DocumentStructure(BaseModel):
    document_id: str
    source_file: str
    parser: Literal["docling"] = "docling"
    parser_version: str | None = None
    pages: list[DocumentPage] = Field(default_factory=list)
    sections: list[DocumentSection] = Field(default_factory=list)
    blocks: list[DocumentBlock] = Field(default_factory=list)
    source_chunks: list[SourceChunk] = Field(default_factory=list)
    assets: list[DocumentAsset] = Field(default_factory=list)
    quality: StructureQuality | None = None
    warnings: list[str] = Field(default_factory=list)
