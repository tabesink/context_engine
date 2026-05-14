from sqlalchemy.orm import Session

from app.domain.models import Evidence
from app.integrations.pageindex_adapter import PageIndexAdapter
from app.storage.repositories.documents import DocumentRepository


class NavigationRetrievalEngine:
    name = "navigation"

    def __init__(self, session: Session, adapter: PageIndexAdapter | None = None):
        self.documents = DocumentRepository(session)
        self.adapter = adapter or PageIndexAdapter()

    def retrieve(
        self,
        *,
        query: str,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
    ) -> list[Evidence]:
        target_documents = document_ids or [doc.id for doc in self.documents.list_ready()]
        evidence: list[Evidence] = []
        for document_id in target_documents:
            parsed = self.documents.get_parsed(document_id)
            navigation = self.documents.get_navigation_index(document_id)
            if not parsed or not navigation:
                continue
            evidence.extend(
                self.adapter.retrieve_sections(
                    query=query,
                    document_id=document_id,
                    pages=parsed.pages,
                    tree=navigation.tree,
                    top_k=top_k,
                )
            )
        return sorted(evidence, key=lambda item: item.score or 0.0, reverse=True)[:top_k]

