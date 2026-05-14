from typing import Protocol

from app.domain.models import Evidence


class RetrievalEngine(Protocol):
    name: str

    def retrieve(
        self,
        *,
        query: str,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
    ) -> list[Evidence]:
        ...

