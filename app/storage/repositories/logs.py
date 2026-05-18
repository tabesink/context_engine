from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.tables import AuditLogRow, QueryLogRow


class LogRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_audit(
        self,
        *,
        actor_id: str | None,
        event: str,
        target_id: str | None,
        metadata: dict,
    ) -> None:
        self.session.add(
            AuditLogRow(actor_id=actor_id, event=event, target_id=target_id, meta=metadata)
        )
        self.session.commit()

    def record_query(
        self,
        *,
        user_id: str,
        query: str,
        mode: str,
        latency_ms: int,
        evidence_count: int,
    ) -> None:
        self.session.add(
            QueryLogRow(
                user_id=user_id,
                query=query,
                mode=mode,
                latency_ms=latency_ms,
                evidence_count=evidence_count,
            )
        )
        self.session.commit()

    def list_audit(self) -> list[AuditLogRow]:
        return list(self.session.scalars(select(AuditLogRow).order_by(AuditLogRow.created_at.desc())))

    def list_queries(self) -> list[QueryLogRow]:
        return list(self.session.scalars(select(QueryLogRow).order_by(QueryLogRow.created_at.desc())))

