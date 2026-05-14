import pytest

from app.domain.models import RetrievalMode
from app.retrieval.routing_policy import RetrievalBackend, RetrievalRoutingPolicy


@pytest.mark.parametrize("mode", list(RetrievalMode))
def test_routing_policy_uses_local_when_lightrag_disabled(mode: RetrievalMode) -> None:
    route = RetrievalRoutingPolicy().resolve(lightrag_enabled=False, mode=mode)

    assert route.backend == RetrievalBackend.LOCAL


@pytest.mark.parametrize(
    "mode",
    [RetrievalMode.AUTO, RetrievalMode.SEMANTIC, RetrievalMode.HYBRID],
)
def test_routing_policy_uses_lightrag_for_remote_modes_when_enabled(mode: RetrievalMode) -> None:
    route = RetrievalRoutingPolicy().resolve(lightrag_enabled=True, mode=mode)

    assert route.backend == RetrievalBackend.LIGHTRAG
    assert route.selected_engine == "lightrag"


def test_routing_policy_keeps_navigation_local_when_lightrag_enabled() -> None:
    route = RetrievalRoutingPolicy().resolve(lightrag_enabled=True, mode=RetrievalMode.NAVIGATION)

    assert route.backend == RetrievalBackend.LOCAL
