from time import perf_counter

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.models import RetrievalResult
from app.integrations.lightrag_remote_adapter import LightRAGAdapterError, lightrag_http_exception
from app.retrieval.answer_composer import AnswerComposer
from app.retrieval.evidence_mapper import to_evidence_response
from app.retrieval.lightrag_remote_engine import LightRAGRemoteRetrievalEngine
from app.retrieval.navigation_engine import NavigationRetrievalEngine
from app.retrieval.routing_policy import RetrievalBackend, RetrievalRoutingPolicy
from app.retrieval.router import RetrievalRouter
from app.retrieval.semantic_engine import SemanticRetrievalEngine
from app.retrieval.strategies import LightRAGRetrievalStrategy, LocalRetrievalStrategy, RetrievalStrategy
from app.schemas.query import QueryRequest, QueryResponse, RetrieveResponse
from app.storage.repositories.logs import LogRepository
from app.storage.tables import UserRow


class RetrievalService:
    def __init__(
        self,
        session: Session,
        *,
        routing_policy: RetrievalRoutingPolicy | None = None,
        local_strategy: RetrievalStrategy | None = None,
        remote_strategy: RetrievalStrategy | None = None,
        answer_composer: AnswerComposer | None = None,
    ):
        self.session = session
        self.settings = get_settings()
        self.router = RetrievalRouter(
            semantic_engine=SemanticRetrievalEngine(session),
            navigation_engine=NavigationRetrievalEngine(session),
        )
        self.remote_engine = LightRAGRemoteRetrievalEngine()
        self.routing_policy = routing_policy or RetrievalRoutingPolicy()
        self.strategies = {
            RetrievalBackend.LOCAL: local_strategy or LocalRetrievalStrategy(self.router),
            RetrievalBackend.LIGHTRAG: remote_strategy or LightRAGRetrievalStrategy(self.remote_engine),
        }
        self.answer_composer = answer_composer or AnswerComposer()

    def retrieve(self, *, request: QueryRequest, user: UserRow) -> RetrieveResponse:
        result = self._retrieve_and_record(request=request, user=user)
        return self._retrieve_response(result, include_debug=request.include_debug and user.role == "admin")

    def _retrieve_and_record(self, *, request: QueryRequest, user: UserRow) -> RetrievalResult:
        started = perf_counter()
        try:
            result = self._retrieve_result(request=request, user=user)
        except LightRAGAdapterError as exc:
            raise lightrag_http_exception(exc) from exc
        latency_ms = int((perf_counter() - started) * 1000)
        LogRepository(self.session).record_query(
            user_id=user.id,
            query=request.query,
            mode=result.mode.value,
            latency_ms=latency_ms,
            evidence_count=len(result.evidence),
        )
        return result

    def _retrieve_result(self, *, request: QueryRequest, user: UserRow) -> RetrievalResult:
        route = self.routing_policy.resolve(
            lightrag_enabled=self.settings.lightrag_enabled,
            mode=request.mode,
        )
        return self.strategies[route.backend].retrieve(
            query=request.query,
            mode=request.mode,
            document_ids=request.document_ids,
            top_k=request.top_k,
            user_id=user.id,
        )

    def answer(self, *, request: QueryRequest, user: UserRow) -> QueryResponse:
        retrieved = self._retrieve_and_record(request=request, user=user)
        answer = self.answer_composer.compose(
            query=request.query,
            evidence=retrieved.evidence,
            allow_general_fallback=request.allow_general_fallback,
        )
        response = self._retrieve_response(
            retrieved,
            include_debug=request.include_debug and user.role == "admin",
        )
        return QueryResponse(**response.model_dump(), answer=answer)

    def _retrieve_response(self, result: RetrievalResult, *, include_debug: bool) -> RetrieveResponse:
        return RetrieveResponse(
            query=result.query,
            mode=result.mode,
            evidence=[to_evidence_response(item) for item in result.evidence],
            debug=result.debug if include_debug else None,
        )

