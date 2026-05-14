from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models import DocumentStatus
from app.indexing.navigation_index_builder import NavigationIndexBuilder
from app.indexing.parsers import DocumentParser
from app.indexing.semantic_index_builder import SemanticIndexBuilder
from app.storage.repositories.documents import DocumentRepository


class IndexingService:
    def __init__(self, session: Session):
        self.documents = DocumentRepository(session)
        self.parser = DocumentParser()
        self.navigation_builder = NavigationIndexBuilder()
        self.semantic_builder = SemanticIndexBuilder()

    def index_document(self, document_id: str) -> None:
        document = self.documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        self.documents.update_status(document, DocumentStatus.INDEXING)
        try:
            parsed = self.parser.parse(
                document_id=UUID(document.id),
                filename=document.filename,
                path=Path(document.storage_path),
                content_type=document.content_type,
            )
            pages = [
                {"number": page.number, "text": page.text, "metadata": page.metadata}
                for page in parsed.pages
            ]
            self.documents.save_parsed(
                document_id=document.id,
                title=parsed.title,
                pages=pages,
                full_text=parsed.full_text,
                metadata=parsed.metadata,
            )
            tree = self.navigation_builder.build(parsed)
            next_version = document.active_index_version + 1
            self.documents.save_navigation_index(
                document_id=document.id,
                tree=tree,
                version=next_version,
            )
            chunks = self.semantic_builder.build(parsed)
            self.documents.replace_semantic_chunks(document_id=document.id, chunks=chunks)
            document.active_index_version = next_version
            self.documents.update_status(document, DocumentStatus.READY)
        except Exception as exc:
            self.documents.update_status(document, DocumentStatus.FAILED, error_message=str(exc))
            raise

