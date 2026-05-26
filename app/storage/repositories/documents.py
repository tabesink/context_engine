from sqlalchemy import delete, or_, select
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
        lightrag_domain_id: str | None = None,
        filename: str,
        content_type: str,
        storage_path: str,
        metadata: dict,
        status: DocumentStatus = DocumentStatus.UPLOADED,
    ) -> DocumentRow:
        document = DocumentRow(
            owner_id=owner_id,
            lightrag_domain_id=lightrag_domain_id,
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
        lightrag_domain_id = DocumentRow.meta["lightrag"]["domain_id"].as_string()
        legacy_lightrag_domain = DocumentRow.meta["lightrag"]["domain"].as_string()
        return list(
            self.session.scalars(
                select(DocumentRow)
                .where(
                    DocumentRow.status == DocumentStatus.READY.value,
                    or_(
                        DocumentRow.lightrag_domain_id == domain_id,
                        lightrag_domain_id == domain_id,
                        legacy_lightrag_domain == domain_id,
                    ),
                )
                .order_by(DocumentRow.created_at.desc())
            )
        )

    def list_all_by_lightrag_domain(self, domain_id: str) -> list[DocumentRow]:
        lightrag_domain_id = DocumentRow.meta["lightrag"]["domain_id"].as_string()
        legacy_lightrag_domain = DocumentRow.meta["lightrag"]["domain"].as_string()
        return list(
            self.session.scalars(
                select(DocumentRow)
                .where(
                    or_(
                        DocumentRow.lightrag_domain_id == domain_id,
                        lightrag_domain_id == domain_id,
                        legacy_lightrag_domain == domain_id,
                    ),
                )
                .order_by(DocumentRow.created_at.desc())
            )
        )

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

    def hard_delete_by_ids(self, document_ids: list[str]) -> int:
        if not document_ids:
            return 0
        result = self.session.execute(delete(DocumentRow).where(DocumentRow.id.in_(document_ids)))
        self.session.commit()
        return int(result.rowcount or 0)

    def audit(self, *, actor_id: str | None, event: str, target_id: str | None, metadata: dict) -> None:
        self.session.add(
            AuditLogRow(actor_id=actor_id, event=event, target_id=target_id, meta=metadata)
        )
        self.session.commit()

