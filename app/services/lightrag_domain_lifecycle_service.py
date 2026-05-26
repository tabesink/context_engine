from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.storage.db import SessionLocal
from app.storage.repositories.lightrag_domain_lifecycle import (
    ACTIVE_DOMAIN_STATES,
    BLOCKED_DOMAIN_STATES,
    LightRAGDomainLifecycleRepository,
)


class LightRAGDomainLifecycleService:
    def __init__(self, session: Session | None = None):
        self._session = session

    @contextmanager
    def _managed_session(self) -> Iterator[Session]:
        if self._session is not None:
            yield self._session
            return
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def state_for(self, domain_id: str) -> str:
        with self._managed_session() as session:
            return LightRAGDomainLifecycleRepository(session).get_state(domain_id)

    def is_active(self, domain_id: str) -> bool:
        return self.state_for(domain_id) in ACTIVE_DOMAIN_STATES

    def blocked_domain_ids(self) -> set[str]:
        with self._managed_session() as session:
            return LightRAGDomainLifecycleRepository(session).list_domain_ids_by_state(
                BLOCKED_DOMAIN_STATES
            )
