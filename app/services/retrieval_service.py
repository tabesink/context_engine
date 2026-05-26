from time import perf_counter

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.models import RetrievalResult
from app.integrations.lightrag_remote_adapter import LightRAGAdapterError, lightrag_http_exception
from app.retrieval.evidence_mapper import to_evidence_response
from app.retrieval.lightrag_remote_engine import LightRAGRemoteRetrievalEngine
from app.retrieval.rich_navigation_engine import RichNavigationEngine
from app.retrieval.routing_policy import RetrievalBackend, RetrievalRoutingPolicy
from app.retrieval.strategies import LightRAGRetrievalStrategy, LocalRetrievalStrategy, RetrievalStrategy
from app.schemas.retrieval import RetrieveRequest, RetrieveResponse
from app.services.lightrag_domain_registry import (
    LightRAGDomainRegistry,
    LightRAGDomainRegistryError,
    lightrag_domain_http_exception,
)
from app.services.retrieval_asset_resolver import RetrievalAssetResolver
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
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
        domain_registry: LightRAGDomainRegistry | None = None,
    ):
        self.session = session
        self.navigation_engine = RichNavigationEngine(session)
        self.remote_engine = LightRAGRemoteRetrievalEngine()
        self.domain_registry = domain_registry or LightRAGDomainRegistry()
        self.routing_policy = routing_policy or RetrievalRoutingPolicy()
        self.strategies = {
            RetrievalBackend.LOCAL: local_strategy or LocalRetrievalStrategy(self.navigation_engine),
            RetrievalBackend.LIGHTRAG: remote_strategy
            or LightRAGRetrievalStrategy(
                self.remote_engine,
                navigation_engine=self.navigation_engine,
            ),
        }

    def retrieve(self, *, request: RetrieveRequest, user: UserRow) -> RetrieveResponse:
        result = self._retrieve_and_record(request=request, user=user)
        return self._retrieve_response(
            result,
            request=request,
            include_debug=request.include_debug and user.role == "admin",
        )

    def _retrieve_and_record(self, *, request: RetrieveRequest, user: UserRow) -> RetrievalResult:
        started = perf_counter()
        try:
            result = self._retrieve_result(request=request, user=user)
        except LightRAGAdapterError as exc:
            raise lightrag_http_exception(exc) from exc
        latency_ms = int((perf_counter() - started) * 1000)
        settings = get_settings()
        LogRepository(self.session).record_query(
            user_id=user.id,
            query=request.query if settings.query_log_store_text else None,
            mode=result.mode.value,
            latency_ms=latency_ms,
            evidence_count=len(result.evidence),
            retention_days=settings.query_log_retention_days,
        )
        return result

    def _retrieve_result(self, *, request: RetrieveRequest, user: UserRow) -> RetrievalResult:
        try:
            self.domain_registry.validate_available(request.lightrag_domain_id)
        except LightRAGDomainRegistryError as exc:
            raise lightrag_domain_http_exception(exc) from exc
        self._validate_lightrag_document_filter(request)
        route = self.routing_policy.resolve(mode=request.mode)
        return self.strategies[route.backend].retrieve(
            query=request.query,
            mode=request.mode,
            document_ids=request.document_ids,
            top_k=request.top_k,
            user_id=user.id,
            lightrag_domain_id=request.lightrag_domain_id,
        )

    def _validate_lightrag_document_filter(self, request: RetrieveRequest) -> None:
        if not request.lightrag_domain_id or not request.document_ids:
            return
        documents = DocumentRepository(self.session)
        for document_id in request.document_ids:
            document = documents.get(document_id)
            metadata = document.meta if document else {}
            lightrag = metadata.get("lightrag", {}) if isinstance(metadata, dict) else {}
            domain_id = lightrag.get("domain_id") or lightrag.get("domain")
            if domain_id != request.lightrag_domain_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Selected documents must belong to LightRAG domain "
                        f"'{request.lightrag_domain_id}'"
                    ),
                )

    def _retrieve_response(
        self,
        result: RetrievalResult,
        *,
        request: RetrieveRequest,
        include_debug: bool,
    ) -> RetrieveResponse:
        assets = []
        if request.include_assets:
            assets = RetrievalAssetResolver(DocumentProcessingRepository(self.session)).resolve(
                result.evidence,
                query=request.query,
                include_thumbnails=request.include_thumbnails,
                max_assets=request.max_assets,
            )
        return RetrieveResponse(
            query=result.query,
            mode=result.mode,
            evidence=[to_evidence_response(item) for item in result.evidence],
            assets=assets,
            debug=result.debug if include_debug else None,
        )

