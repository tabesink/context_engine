from pydantic import BaseModel, Field

from app.domain.models import RetrievalMode


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: RetrievalMode = RetrievalMode.AUTO
    document_ids: list[str] | None = None
    lightrag_domain_id: str | None = None
    top_k: int = Field(default=8, ge=1, le=30)
    include_debug: bool = False
    include_assets: bool = False
    include_thumbnails: bool = True
    max_assets: int = Field(default=5, ge=0, le=20)


class EvidenceResponse(BaseModel):
    evidence_id: str
    document_id: str
    source_engine: str
    text: str
    score: float | None = None
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    source_path: str | None = None
    document_title: str | None = None
    chunk_id: str | None = None
    reference_id: str | None = None
    workspace_node_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class AssetResponse(BaseModel):
    asset_id: str
    document_id: str
    asset_type: str
    caption: str | None = None
    page_number: int | None = None
    url: str
    thumbnail_url: str | None = None


class RetrieveResponse(BaseModel):
    query: str
    mode: RetrievalMode
    evidence: list[EvidenceResponse]
    assets: list[AssetResponse] = Field(default_factory=list)
    debug: dict | None = None
