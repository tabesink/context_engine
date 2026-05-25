from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import DocumentStatus


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict)
    error_message: str | None = None


class UploadResponse(BaseModel):
    document: DocumentResponse
    job_id: str | None = None


class PageResponse(BaseModel):
    document_id: str
    page_number: int
    text: str
    metadata: dict = Field(default_factory=dict)


class StructureResponse(BaseModel):
    document_id: str
    tree: list[dict]
    source: str = "navigation"
    pages: list[dict] = Field(default_factory=list)
    sections: list[dict] = Field(default_factory=list)
    blocks: list[dict] = Field(default_factory=list)
    source_chunks: list[dict] = Field(default_factory=list)
    assets: list[dict] = Field(default_factory=list)


class StructureQualityResponse(BaseModel):
    document_id: str
    heading_count: int
    section_count: int
    block_count: int
    asset_count: int
    has_toc: bool
    has_page_ranges: bool
    has_deep_hierarchy: bool
    unsectioned_block_ratio: float
    invalid_page_range_count: int
    score: float
    reasons: list[str] = Field(default_factory=list)


class SectionDetailResponse(BaseModel):
    document_id: str
    section: dict
    blocks: list[dict] = Field(default_factory=list)
    source_chunks: list[dict] = Field(default_factory=list)
    assets: list[dict] = Field(default_factory=list)


class SourceChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    section_id: str | None = None
    block_ids: list[str]
    text: str
    page_start: int | None = None
    page_end: int | None = None
    asset_ids: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

