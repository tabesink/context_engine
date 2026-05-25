from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.integrations.lightrag_remote_adapter import (
    LightRAGAdapterError,
    LightRAGRemoteAdapter,
    lightrag_http_exception,
)
from app.storage.tables import UserRow

router = APIRouter(tags=["lightrag"])


@router.get("/lightrag/domains/{domain_id}/graphs")
def get_graphs(
    domain_id: str,
    label: str = Query(...),
    max_depth: int = Query(3, ge=1),
    max_nodes: int = Query(1000, ge=1),
    user: UserRow = Depends(get_current_user),
):
    del user
    return _proxy_get(
        "/graphs",
        domain_id=domain_id,
        params={"label": label, "max_depth": max_depth, "max_nodes": max_nodes},
    )


@router.get("/lightrag/domains/{domain_id}/graph/labels")
def get_graph_labels(domain_id: str, user: UserRow = Depends(get_current_user)):
    del user
    return _proxy_get("/graph/label/list", domain_id=domain_id)


@router.get("/lightrag/domains/{domain_id}/graph/labels/popular")
def get_popular_graph_labels(
    domain_id: str,
    limit: int = Query(300, ge=1, le=1000),
    user: UserRow = Depends(get_current_user),
):
    del user
    return _proxy_get("/graph/label/popular", domain_id=domain_id, params={"limit": limit})


@router.get("/lightrag/domains/{domain_id}/graph/labels/search")
def search_graph_labels(
    domain_id: str,
    q: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
    user: UserRow = Depends(get_current_user),
):
    del user
    return _proxy_get("/graph/label/search", domain_id=domain_id, params={"q": q, "limit": limit})


def _proxy_get(path: str, *, domain_id: str, params: dict | None = None):
    try:
        return LightRAGRemoteAdapter.for_domain(domain_id).get_json(path, params=params)
    except LightRAGAdapterError as exc:
        raise lightrag_http_exception(exc) from exc
