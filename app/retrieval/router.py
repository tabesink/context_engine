from app.domain.models import RetrievalMode, RetrievalResult
from app.retrieval.base import RetrievalEngine
from app.retrieval.hybrid_merger import HybridMerger


NAVIGATION_TERMS = {
    "page",
    "section",
    "chapter",
    "where",
    "show",
    "exact",
    "manual",
    "table",
    "installation",
    "instructions",
    "step",
    "maintenance",
    "appendix",
}

SEMANTIC_TERMS = {
    "compare",
    "summarize",
    "relationship",
    "related",
    "common",
    "themes",
    "entities",
    "suppliers",
    "products",
    "policies",
    "similar",
}


class RetrievalRouter:
    def __init__(
        self,
        *,
        semantic_engine: RetrievalEngine,
        navigation_engine: RetrievalEngine,
        merger: HybridMerger | None = None,
    ):
        self.semantic_engine = semantic_engine
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
    ) -> RetrievalResult:
        selected_mode = self.classify(query) if mode == RetrievalMode.AUTO else mode
        debug = {"requested_mode": mode.value, "selected_mode": selected_mode.value}

        if selected_mode == RetrievalMode.SEMANTIC:
            evidence = self.semantic_engine.retrieve(
                query=query, document_ids=document_ids, top_k=top_k, user_id=user_id
            )
            return RetrievalResult(query=query, mode=selected_mode, evidence=evidence, debug=debug)

        if selected_mode == RetrievalMode.NAVIGATION:
            evidence = self.navigation_engine.retrieve(
                query=query, document_ids=document_ids, top_k=top_k, user_id=user_id
            )
            return RetrievalResult(query=query, mode=selected_mode, evidence=evidence, debug=debug)

        semantic = self.semantic_engine.retrieve(
            query=query, document_ids=document_ids, top_k=top_k, user_id=user_id
        )
        navigation = self.navigation_engine.retrieve(
            query=query, document_ids=document_ids, top_k=top_k, user_id=user_id
        )
        evidence = self.merger.merge(semantic + navigation, top_k=top_k)
        debug["engines"] = ["semantic", "navigation"]
        return RetrievalResult(query=query, mode=selected_mode, evidence=evidence, debug=debug)

    def classify(self, query: str) -> RetrievalMode:
        terms = set(query.lower().replace("?", " ").split())
        if terms & NAVIGATION_TERMS and terms & SEMANTIC_TERMS:
            return RetrievalMode.HYBRID
        if terms & NAVIGATION_TERMS:
            return RetrievalMode.NAVIGATION
        if terms & SEMANTIC_TERMS:
            return RetrievalMode.SEMANTIC
        return RetrievalMode.HYBRID

