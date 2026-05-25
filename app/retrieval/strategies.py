from typing import Protocol

from app.domain.models import RetrievalMode, RetrievalResult
from app.retrieval.hybrid_merger import HybridMerger
from app.retrieval.lightrag_remote_engine import LightRAGRemoteRetrievalEngine
from app.retrieval.rich_navigation_engine import RichNavigationEngine


class RetrievalStrategy(Protocol):
    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
        lightrag_domain_id: str | None = None,
    ) -> RetrievalResult:
        ...


class LocalRetrievalStrategy:
    def __init__(self, navigation_engine: RichNavigationEngine):
        self.navigation_engine = navigation_engine

    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
        lightrag_domain_id: str | None = None,
    ) -> RetrievalResult:
        del lightrag_domain_id
        evidence = self.navigation_engine.retrieve(
            query=query,
            document_ids=document_ids,
            top_k=top_k,
            user_id=user_id,
        )
        return RetrievalResult(
            query=query,
            mode=mode,
            evidence=evidence,
            debug={"requested_mode": mode.value, "selected_engine": "navigation"},
        )


class LightRAGRetrievalStrategy:
    def __init__(
        self,
        engine: LightRAGRemoteRetrievalEngine,
        *,
        navigation_engine: RichNavigationEngine | None = None,
        merger: HybridMerger | None = None,
    ):
        self.engine = engine
        self.navigation_engine = navigation_engine
        self.merger = merger or HybridMerger()

    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
        lightrag_domain_id: str | None = None,
    ) -> RetrievalResult:
        if mode == RetrievalMode.NAVIGATION and self.navigation_engine is not None:
            evidence = self.navigation_engine.retrieve(
                query=query,
                document_ids=document_ids,
                top_k=top_k,
                user_id=user_id,
            )
            return RetrievalResult(
                query=query,
                mode=mode,
                evidence=evidence,
                debug={"requested_mode": mode.value, "selected_engine": "navigation"},
            )

        semantic = self.engine.retrieve(
            query=query,
            mode=mode,
            document_ids=document_ids,
            lightrag_domain_id=lightrag_domain_id,
            top_k=top_k,
            user_id=user_id,
        )
        evidence = semantic
        selected_engine = self.engine.name
        if mode == RetrievalMode.HYBRID and self.navigation_engine is not None:
            navigation = self.navigation_engine.retrieve(
                query=query,
                document_ids=document_ids,
                top_k=top_k,
                user_id=user_id,
            )
            evidence = self.merger.merge(semantic + navigation, top_k=top_k)
            selected_engine = "lightrag+navigation"
        return RetrievalResult(
            query=query,
            mode=mode,
            evidence=evidence,
            debug={"requested_mode": mode.value, "selected_engine": selected_engine},
        )
