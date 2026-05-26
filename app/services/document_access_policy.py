from app.core.errors import not_found
from app.domain.models import DocumentStatus
from app.services.lightrag_domain_lifecycle_service import LightRAGDomainLifecycleService
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow, UserRow


class DocumentAccessPolicy:
    """V1 shared-corpus document access policy.

    Any authenticated user may read ready documents. Keeping the rule here prevents
    new document surfaces from reimplementing status checks route by route.
    """

    def __init__(
        self,
        documents: DocumentRepository,
        *,
        lifecycle: LightRAGDomainLifecycleService | None = None,
    ):
        self.documents = documents
        self.lifecycle = lifecycle or LightRAGDomainLifecycleService()

    def _is_domain_active(self, document: DocumentRow) -> bool:
        domain_id = (document.lightrag_domain_id or "").strip()
        if not domain_id:
            metadata = document.meta if isinstance(document.meta, dict) else {}
            lightrag = metadata.get("lightrag", {}) if isinstance(metadata, dict) else {}
            domain_id = str(lightrag.get("domain_id") or lightrag.get("domain") or "").strip()
        if not domain_id:
            return True
        return self.lifecycle.is_active(domain_id)

    def list_readable_documents(self, user: UserRow) -> list[DocumentRow]:
        del user
        return [document for document in self.documents.list_ready() if self._is_domain_active(document)]

    def filter_readable_documents(
        self,
        user: UserRow,
        documents: list[DocumentRow],
    ) -> list[DocumentRow]:
        del user
        return [
            document
            for document in documents
            if document.status == DocumentStatus.READY.value
            and self._is_domain_active(document)
        ]

    def get_readable_document_or_404(self, *, user: UserRow, document_id: str) -> DocumentRow:
        del user
        document = self.documents.get(document_id)
        if (
            not document
            or document.status != DocumentStatus.READY.value
            or not self._is_domain_active(document)
        ):
            raise not_found("Document not found")
        return document
