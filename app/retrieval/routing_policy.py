from dataclasses import dataclass
from enum import StrEnum

from app.domain.models import RetrievalMode


class RetrievalBackend(StrEnum):
    LOCAL = "local"
    LIGHTRAG = "lightrag"


@dataclass(frozen=True)
class RetrievalRoute:
    backend: RetrievalBackend
    selected_engine: str


class RetrievalRoutingPolicy:
    remote_modes = frozenset({RetrievalMode.AUTO, RetrievalMode.SEMANTIC, RetrievalMode.HYBRID})

    def resolve(self, *, mode: RetrievalMode) -> RetrievalRoute:
        if mode == RetrievalMode.NAVIGATION:
            return RetrievalRoute(backend=RetrievalBackend.LOCAL, selected_engine="navigation")
        if mode in self.remote_modes:
            return RetrievalRoute(backend=RetrievalBackend.LIGHTRAG, selected_engine="lightrag")
        return RetrievalRoute(backend=RetrievalBackend.LIGHTRAG, selected_engine="lightrag")
