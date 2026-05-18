from pydantic import BaseModel, Field

from app.domain.models import RetrievalMode


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: RetrievalMode = RetrievalMode.AUTO
    document_ids: list[str] | None = None
    lightrag_domain_id: str | None = None
    top_k: int = Field(default=8, ge=1, le=30)
    include_debug: bool = False
    allow_general_fallback: bool = False


class EvidenceResponse(BaseModel):
    evidence_id: str
    document_id: str
    source_engine: str
    text: str
    score: float | None = None
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    metadata: dict = {}


class RetrieveResponse(BaseModel):
    query: str
    mode: RetrievalMode
    evidence: list[EvidenceResponse]
    debug: dict | None = None


class QueryResponse(RetrieveResponse):
    answer: str

