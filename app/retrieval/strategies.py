from typing import Protocol

from app.domain.models import RetrievalMode, RetrievalResult
from app.retrieval.lightrag_remote_engine import LightRAGRemoteRetrievalEngine
from app.retrieval.router import RetrievalRouter


class RetrievalStrategy(Protocol):
    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
    ) -> RetrievalResult:
        ...


class LocalRetrievalStrategy:
    def __init__(self, router: RetrievalRouter):
        self.router = router

    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
    ) -> RetrievalResult:
        return self.router.retrieve(
            query=query,
            mode=mode,
            document_ids=document_ids,
            top_k=top_k,
            user_id=user_id,
        )


class LightRAGRetrievalStrategy:
    def __init__(self, engine: LightRAGRemoteRetrievalEngine):
        self.engine = engine

    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
    ) -> RetrievalResult:
        evidence = self.engine.retrieve(
            query=query,
            mode=mode,
            document_ids=document_ids,
            top_k=top_k,
            user_id=user_id,
        )
        return RetrievalResult(
            query=query,
            mode=mode,
            evidence=evidence,
            debug={"requested_mode": mode.value, "selected_engine": self.engine.name},
        )
