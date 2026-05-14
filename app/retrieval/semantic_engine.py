from sqlalchemy.orm import Session

from app.domain.models import Evidence
from app.integrations.lightrag_adapter import LightRAGAdapter
from app.storage.repositories.documents import DocumentRepository


class SemanticRetrievalEngine:
    name = "semantic"

    def __init__(self, session: Session, adapter: LightRAGAdapter | None = None):
        self.documents = DocumentRepository(session)
        self.adapter = adapter or LightRAGAdapter()

    def retrieve(
        self,
        *,
        query: str,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
    ) -> list[Evidence]:
        query_embedding = self.adapter.embed(query)
        scored: list[tuple[float, Evidence]] = []
        for chunk in self.documents.list_semantic_chunks(document_ids):
            score = self.adapter.score(query_embedding, chunk.embedding)
            if score <= 0:
                continue
            scored.append((score, self.adapter.to_evidence(chunk, score)))
        return [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:top_k]]

