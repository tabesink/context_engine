from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import DocumentStatus, utc_now
from app.storage.tables import (
    AuditLogRow,
    DocumentRow,
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

    def list_ready_by_lightrag_domain(self, domain_id: str) -> list[DocumentRow]:
        documents = self.list_ready()
        matched: list[DocumentRow] = []
        for document in documents:
            metadata = document.meta if isinstance(document.meta, dict) else {}
            lightrag = metadata.get("lightrag") if isinstance(metadata.get("lightrag"), dict) else {}
            document_domain_id = lightrag.get("domain_id") or lightrag.get("domain")
            if document_domain_id == domain_id:
                matched.append(document)
        return matched

    def list_all(self, *, limit: int = 50, offset: int = 0) -> list[DocumentRow]:
        return list(
            self.session.scalars(
                select(DocumentRow).order_by(DocumentRow.created_at.desc()).limit(limit).offset(offset)
            )
        )

    def list_lightrag_indexing(self) -> list[DocumentRow]:
        documents = list(
            self.session.scalars(
                select(DocumentRow)
                .where(DocumentRow.status == DocumentStatus.INDEXING.value)
                .order_by(DocumentRow.created_at.desc())
            )
        )
        pending: list[DocumentRow] = []
        for document in documents:
            lightrag = document.meta.get("lightrag", {}) if isinstance(document.meta, dict) else {}
            if (
                document.status == DocumentStatus.INDEXING.value
                and lightrag.get("track_id")
                and lightrag.get("status") == "indexing"
            ):
                pending.append(document)
        return pending

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

    def audit(self, *, actor_id: str | None, event: str, target_id: str | None, metadata: dict) -> None:
        self.session.add(
            AuditLogRow(actor_id=actor_id, event=event, target_id=target_id, meta=metadata)
        )
        self.session.commit()

