from datetime import datetime

from pydantic import BaseModel

from app.domain.models import DocumentStatus


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict = {}
    error_message: str | None = None


class UploadResponse(BaseModel):
    document: DocumentResponse
    job_id: str | None = None


class RebuildStructureRequest(BaseModel):
    enable_toc_refinement: str = "auto"
    preserve_assets: bool = True


class PageResponse(BaseModel):
    document_id: str
    page_number: int
    text: str
    metadata: dict = {}


class StructureResponse(BaseModel):
    document_id: str
    tree: list[dict]
    source: str = "navigation"
    sections: list[dict] = []
    blocks: list[dict] = []
    source_chunks: list[dict] = []
    assets: list[dict] = []


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
    should_run_toc_refiner: bool
    reasons: list[str] = []


class SectionDetailResponse(BaseModel):
    document_id: str
    section: dict
    blocks: list[dict] = []
    source_chunks: list[dict] = []
    assets: list[dict] = []


class SourceChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    section_id: str | None = None
    block_ids: list[str]
    text: str
    page_start: int | None = None
    page_end: int | None = None
    asset_ids: list[str] = []
    metadata: dict = {}


class TocRefinementReportResponse(BaseModel):
    document_id: str
    enabled: bool
    accepted: bool
    reason: str | None = None
    validation_accuracy: float | None = None
    logical_to_physical_offset: int | None = None
    llm_call_count: int
    warnings: list[str] = []

