from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import utc_now
from app.storage.tables import LightRAGDomainLifecycleRow


ACTIVE_DOMAIN_STATES = {"active"}
BLOCKED_DOMAIN_STATES = {"archiving", "archived", "purging", "purged", "failed"}


class LightRAGDomainLifecycleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, domain_id: str) -> LightRAGDomainLifecycleRow | None:
        return self.session.get(LightRAGDomainLifecycleRow, domain_id)

    def list_domain_ids_by_state(self, states: set[str]) -> set[str]:
        if not states:
            return set()
        rows = self.session.scalars(
            select(LightRAGDomainLifecycleRow.domain_id).where(
                LightRAGDomainLifecycleRow.state.in_(sorted(states))
            )
        )
        return set(rows)

    def get_state(self, domain_id: str) -> str:
        row = self.get(domain_id)
        return row.state if row else "active"

    def set_state(
        self,
        *,
        domain_id: str,
        state: str,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> LightRAGDomainLifecycleRow:
        row = self.get(domain_id)
        if row is None:
            row = LightRAGDomainLifecycleRow(
                domain_id=domain_id,
                state=state,
                error_message=error_message,
                meta=metadata or {},
            )
            self.session.add(row)
        else:
            row.state = state
            row.error_message = error_message
            if metadata is not None:
                row.meta = metadata
            row.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(row)
        return row
