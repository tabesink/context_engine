import pytest

from app.domain.models import RetrievalMode
from app.retrieval.routing_policy import RetrievalBackend, RetrievalRoutingPolicy


@pytest.mark.parametrize(
    "mode",
    [RetrievalMode.AUTO, RetrievalMode.SEMANTIC, RetrievalMode.HYBRID],
)
def test_routing_policy_uses_lightrag_for_semantic_modes(mode: RetrievalMode) -> None:
    route = RetrievalRoutingPolicy().resolve(mode=mode)

    assert route.backend == RetrievalBackend.LIGHTRAG
    assert route.selected_engine == "lightrag"


def test_routing_policy_keeps_navigation_local() -> None:
    route = RetrievalRoutingPolicy().resolve(mode=RetrievalMode.NAVIGATION)

    assert route.backend == RetrievalBackend.LOCAL
    assert route.selected_engine == "navigation"
