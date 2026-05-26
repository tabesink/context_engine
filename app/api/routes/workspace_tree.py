from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.schemas.workspace_tree import WorkspaceTreeResponse
from app.services.lightrag_domain_registry import (
    LightRAGDomainRegistry,
    LightRAGDomainRegistryError,
    lightrag_domain_http_exception,
)
from app.services.workspace_tree_service import WorkspaceTreeService
from app.storage.db import get_session
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/lightrag/domains", tags=["workspace-tree"])


def get_domain_registry() -> LightRAGDomainRegistry:
    return LightRAGDomainRegistry()


@router.get("/{domain_id}/workspace-tree")
def get_workspace_tree(
    domain_id: str,
    depth: int | None = Query(default=None, ge=1),
    include_assets: bool = Query(default=True),
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
    domain_registry: LightRAGDomainRegistry = Depends(get_domain_registry),
) -> WorkspaceTreeResponse:
    service = WorkspaceTreeService(
        documents=DocumentRepository(session),
        processing=DocumentProcessingRepository(session),
        domain_registry=domain_registry,
    )
    try:
        return service.build_for_domain(
            domain_id=domain_id,
            user=user,
            depth=depth,
            include_assets=include_assets,
        )
    except LightRAGDomainRegistryError as exc:
        raise lightrag_domain_http_exception(exc) from exc
