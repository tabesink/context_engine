from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.integrations.lightrag_remote_adapter import (
    LightRAGAdapterError,
    LightRAGRemoteAdapter,
    lightrag_http_exception,
)
from app.storage.tables import UserRow

router = APIRouter(tags=["lightrag"])


@router.get("/graphs")
def get_graphs(
    label: str = Query(...),
    max_depth: int = Query(3, ge=1),
    max_nodes: int = Query(1000, ge=1),
    user: UserRow = Depends(get_current_user),
):
    del user
    return _proxy_get(
        "/graphs",
        params={"label": label, "max_depth": max_depth, "max_nodes": max_nodes},
    )


@router.get("/graph/label/list")
def get_graph_labels(user: UserRow = Depends(get_current_user)):
    del user
    return _proxy_get("/graph/label/list")


@router.get("/graph/label/popular")
def get_popular_graph_labels(
    limit: int = Query(300, ge=1, le=1000),
    user: UserRow = Depends(get_current_user),
):
    del user
    return _proxy_get("/graph/label/popular", params={"limit": limit})


@router.get("/graph/label/search")
def search_graph_labels(
    q: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
    user: UserRow = Depends(get_current_user),
):
    del user
    return _proxy_get("/graph/label/search", params={"q": q, "limit": limit})


def _proxy_get(path: str, *, params: dict | None = None):
    try:
        return LightRAGRemoteAdapter.for_domain().get_json(path, params=params)
    except LightRAGAdapterError as exc:
        raise lightrag_http_exception(exc) from exc
