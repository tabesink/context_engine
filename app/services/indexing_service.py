from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models import DocumentStatus
from app.indexing.navigation_index_builder import NavigationIndexBuilder
from app.indexing.parsers import DocumentParser
from app.storage.repositories.documents import DocumentRepository


class IndexingService:
    def __init__(self, session: Session):
        self.documents = DocumentRepository(session)
        self.parser = DocumentParser()
        self.navigation_builder = NavigationIndexBuilder()

    def index_document(self, document_id: str) -> None:
        document = self.documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        metadata = document.meta | {
            "navigation": {
                **(document.meta.get("navigation") or {}),
                "enabled": True,
                "status": "processing",
            }
        }
        document = self.documents.update_metadata(document, metadata)
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
            document.active_index_version = next_version
            metadata = document.meta | {
                "navigation": {
                    **(document.meta.get("navigation") or {}),
                    "enabled": True,
                    "status": "ready",
                    "parsed_pages_available": True,
                    "navigation_index_available": True,
                }
            }
            document = self.documents.update_metadata(document, metadata)
            if document.meta.get("semantic_engine") != "lightrag":
                self.documents.update_status(document, DocumentStatus.READY)
        except Exception as exc:
            metadata = document.meta | {
                "navigation": {
                    **(document.meta.get("navigation") or {}),
                    "enabled": True,
                    "status": "failed",
                    "message": str(exc),
                }
            }
            document = self.documents.update_metadata(document, metadata)
            if document.meta.get("semantic_engine") != "lightrag":
                self.documents.update_status(document, DocumentStatus.FAILED, error_message=str(exc))
            raise

