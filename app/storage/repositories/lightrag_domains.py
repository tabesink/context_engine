from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import utc_now
from app.storage.tables import LightRAGDomainRow


class LightRAGDomainRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, domain_id: str) -> LightRAGDomainRow | None:
        return self.session.get(LightRAGDomainRow, domain_id)

    def list(self, *, limit: int = 200, offset: int = 0) -> list[LightRAGDomainRow]:
        return list(
            self.session.scalars(
                select(LightRAGDomainRow)
                .order_by(LightRAGDomainRow.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def upsert(
        self,
        *,
        domain_id: str,
        display_name: str | None = None,
        state: str | None = None,
        health_status: str | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> LightRAGDomainRow:
        row = self.get(domain_id)
        if row is None:
            row = LightRAGDomainRow(
                id=domain_id,
                display_name=(display_name or domain_id),
                state=state or "active",
                health_status=health_status,
                error_message=error_message,
                meta=metadata or {},
            )
            self.session.add(row)
        else:
            if display_name is not None:
                row.display_name = display_name
            if state is not None:
                row.state = state
            if health_status is not None:
                row.health_status = health_status
            if error_message is not None:
                row.error_message = error_message
            if metadata is not None:
                row.meta = metadata
            row.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(row)
        return row
