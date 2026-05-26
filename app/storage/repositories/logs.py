from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.models import utc_now
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
        query: str | None,
        mode: str,
        latency_ms: int,
        evidence_count: int,
        retention_days: int | None = None,
    ) -> None:
        self.session.add(
            QueryLogRow(
                user_id=user_id,
                query=query or "",
                mode=mode,
                latency_ms=latency_ms,
                evidence_count=evidence_count,
            )
        )
        if retention_days is not None and retention_days > 0:
            self.purge_queries_older_than(days=retention_days)
        self.session.commit()

    def list_audit(self, *, limit: int = 100, offset: int = 0) -> list[AuditLogRow]:
        return list(
            self.session.scalars(
                select(AuditLogRow).order_by(AuditLogRow.created_at.desc()).limit(limit).offset(offset)
            )
        )

    def list_queries(self, *, limit: int = 100, offset: int = 0) -> list[QueryLogRow]:
        return list(
            self.session.scalars(
                select(QueryLogRow).order_by(QueryLogRow.created_at.desc()).limit(limit).offset(offset)
            )
        )

    def purge_queries_older_than(self, *, days: int) -> None:
        cutoff = utc_now() - timedelta(days=days)
        self.session.execute(delete(QueryLogRow).where(QueryLogRow.created_at < cutoff))

