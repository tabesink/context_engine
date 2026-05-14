import hashlib
import math
from uuid import UUID

from app.domain.models import Evidence, PageRef
from app.storage.tables import SemanticChunkRow


class LightRAGAdapter:
    """Local adapter boundary for LightRAG-style semantic retrieval.

    V1 uses deterministic hashed embeddings so tests and local development do not need an
    external embedding service. The adapter can later delegate to real LightRAG internals.
    """

    dimensions = 64

    def embed(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def score(self, query_embedding: list[float], chunk_embedding: list[float]) -> float:
        return sum(left * right for left, right in zip(query_embedding, chunk_embedding, strict=False))

    def to_evidence(self, chunk: SemanticChunkRow, score: float) -> Evidence:
        return Evidence(
            id=chunk.id,
            document_id=UUID(chunk.document_id),
            source_engine="semantic",
            text=chunk.text,
            score=score,
            page_ref=PageRef(
                document_id=UUID(chunk.document_id),
                page_start=chunk.page_start,
                page_end=chunk.page_end,
            ),
            metadata=chunk.meta | {"chunk_index": chunk.chunk_index},
        )

