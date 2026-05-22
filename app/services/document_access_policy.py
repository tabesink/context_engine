from app.core.errors import not_found
from app.domain.models import DocumentStatus
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow, UserRow


class DocumentAccessPolicy:
    """V1 shared-corpus document access policy.

    Any authenticated user may read ready documents. Keeping the rule here prevents
    new document surfaces from reimplementing status checks route by route.
    """

    def __init__(self, documents: DocumentRepository):
        self.documents = documents

    def list_readable_documents(self, user: UserRow) -> list[DocumentRow]:
        del user
        return self.documents.list_ready()

    def get_readable_document_or_404(self, *, user: UserRow, document_id: str) -> DocumentRow:
        del user
        document = self.documents.get(document_id)
        if not document or document.status != DocumentStatus.READY.value:
            raise not_found("Document not found")
        return document
