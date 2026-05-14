from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import DocumentStatus, utc_now
from app.storage.tables import (
    AuditLogRow,
    DocumentRow,
    NavigationIndexRow,
    ParsedDocumentRow,
    SemanticChunkRow,
)


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        owner_id: str | None,
        filename: str,
        content_type: str,
        storage_path: str,
        metadata: dict,
        status: DocumentStatus = DocumentStatus.UPLOADED,
    ) -> DocumentRow:
        document = DocumentRow(
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            storage_path=storage_path,
            status=status.value,
            meta=metadata,
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def update_metadata(self, document: DocumentRow, metadata: dict) -> DocumentRow:
        document.meta = metadata
        document.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(document)
        return document

    def get(self, document_id: str) -> DocumentRow | None:
        return self.session.get(DocumentRow, document_id)

    def list_ready(self) -> list[DocumentRow]:
        return list(
            self.session.scalars(
                select(DocumentRow)
                .where(DocumentRow.status == DocumentStatus.READY.value)
                .order_by(DocumentRow.created_at.desc())
            )
        )

    def list_all(self) -> list[DocumentRow]:
        return list(self.session.scalars(select(DocumentRow).order_by(DocumentRow.created_at.desc())))

    def update_status(
        self,
        document: DocumentRow,
        status: DocumentStatus,
        *,
        error_message: str | None = None,
    ) -> DocumentRow:
        document.status = status.value
        document.error_message = error_message
        document.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(document)
        return document

    def mark_deleted(self, document: DocumentRow) -> DocumentRow:
        return self.update_status(document, DocumentStatus.DELETED)

    def save_parsed(self, *, document_id: str, title: str, pages: list, full_text: str, metadata: dict) -> None:
        existing = self.session.get(ParsedDocumentRow, document_id)
        if existing:
            existing.title = title
            existing.pages = pages
            existing.full_text = full_text
            existing.meta = metadata
        else:
            self.session.add(
                ParsedDocumentRow(
                    document_id=document_id,
                    title=title,
                    pages=pages,
                    full_text=full_text,
                    meta=metadata,
                )
            )
        self.session.commit()

    def get_parsed(self, document_id: str) -> ParsedDocumentRow | None:
        return self.session.get(ParsedDocumentRow, document_id)

    def save_navigation_index(self, *, document_id: str, tree: list, version: int) -> None:
        existing = self.session.get(NavigationIndexRow, document_id)
        if existing:
            existing.tree = tree
            existing.version = version
        else:
            self.session.add(NavigationIndexRow(document_id=document_id, tree=tree, version=version))
        self.session.commit()

    def get_navigation_index(self, document_id: str) -> NavigationIndexRow | None:
        return self.session.get(NavigationIndexRow, document_id)

    def replace_semantic_chunks(self, *, document_id: str, chunks: list[SemanticChunkRow]) -> None:
        existing = self.session.scalars(
            select(SemanticChunkRow).where(SemanticChunkRow.document_id == document_id)
        )
        for chunk in existing:
            self.session.delete(chunk)
        for chunk in chunks:
            self.session.add(chunk)
        self.session.commit()

    def list_semantic_chunks(self, document_ids: list[str] | None = None) -> list[SemanticChunkRow]:
        query = select(SemanticChunkRow)
        if document_ids:
            query = query.where(SemanticChunkRow.document_id.in_(document_ids))
        return list(self.session.scalars(query))

    def audit(self, *, actor_id: str | None, event: str, target_id: str | None, metadata: dict) -> None:
        self.session.add(
            AuditLogRow(actor_id=actor_id, event=event, target_id=target_id, meta=metadata)
        )
        self.session.commit()

