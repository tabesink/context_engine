from time import perf_counter

from sqlalchemy.orm import Session

from app.domain.models import Evidence, RetrievalResult
from app.retrieval.answer_composer import AnswerComposer
from app.retrieval.navigation_engine import NavigationRetrievalEngine
from app.retrieval.router import RetrievalRouter
from app.retrieval.semantic_engine import SemanticRetrievalEngine
from app.schemas.query import EvidenceResponse, QueryRequest, QueryResponse, RetrieveResponse
from app.storage.repositories.logs import LogRepository
from app.storage.tables import UserRow


class RetrievalService:
    def __init__(self, session: Session):
        self.session = session
        self.router = RetrievalRouter(
            semantic_engine=SemanticRetrievalEngine(session),
            navigation_engine=NavigationRetrievalEngine(session),
        )
        self.answer_composer = AnswerComposer()

    def retrieve(self, *, request: QueryRequest, user: UserRow) -> RetrieveResponse:
        started = perf_counter()
        result = self.router.retrieve(
            query=request.query,
            mode=request.mode,
            document_ids=request.document_ids,
            top_k=request.top_k,
            user_id=user.id,
        )
        latency_ms = int((perf_counter() - started) * 1000)
        LogRepository(self.session).record_query(
            user_id=user.id,
            query=request.query,
            mode=result.mode.value,
            latency_ms=latency_ms,
            evidence_count=len(result.evidence),
        )
        return self._retrieve_response(result, include_debug=request.include_debug and user.role == "admin")

    def answer(self, *, request: QueryRequest, user: UserRow) -> QueryResponse:
        retrieved = self.retrieve(request=request, user=user)
        answer = self.answer_composer.compose(
            query=request.query,
            evidence=[
                self._response_to_evidence(item)
                for item in retrieved.evidence
            ],
            allow_general_fallback=request.allow_general_fallback,
        )
        return QueryResponse(**retrieved.model_dump(), answer=answer)

    def _retrieve_response(self, result: RetrievalResult, *, include_debug: bool) -> RetrieveResponse:
        return RetrieveResponse(
            query=result.query,
            mode=result.mode,
            evidence=[self._evidence_response(item) for item in result.evidence],
            debug=result.debug if include_debug else None,
        )

    def _evidence_response(self, evidence: Evidence) -> EvidenceResponse:
        return EvidenceResponse(
            evidence_id=evidence.id,
            document_id=str(evidence.document_id),
            source_engine=evidence.source_engine,
            text=evidence.text,
            score=evidence.score,
            page_start=evidence.page_ref.page_start if evidence.page_ref else None,
            page_end=evidence.page_ref.page_end if evidence.page_ref else None,
            section_title=evidence.section_ref.title if evidence.section_ref else None,
            metadata=evidence.metadata,
        )

    def _response_to_evidence(self, response: EvidenceResponse) -> Evidence:
        from uuid import UUID

        from app.domain.models import PageRef

        return Evidence(
            id=response.evidence_id,
            document_id=UUID(response.document_id),
            source_engine=response.source_engine,
            text=response.text,
            score=response.score,
            page_ref=PageRef(
                document_id=UUID(response.document_id),
                page_start=response.page_start,
                page_end=response.page_end,
            ),
            metadata=response.metadata,
        )

