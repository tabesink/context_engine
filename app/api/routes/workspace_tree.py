from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.lightrag_deploy.errors import DomainNotFoundError
from app.lightrag_deploy.service import LightRAGDomainService
from app.schemas.workspace_tree import WorkspaceTreeResponse
from app.services.workspace_tree_service import WorkspaceTreeService
from app.storage.db import get_session
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/lightrag/domains", tags=["workspace-tree"])


def get_domain_service() -> LightRAGDomainService:
    return LightRAGDomainService()


@router.get("/{domain_id}/workspace-tree")
def get_workspace_tree(
    domain_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
    domain_service: LightRAGDomainService = Depends(get_domain_service),
) -> WorkspaceTreeResponse:
    service = WorkspaceTreeService(
        documents=DocumentRepository(session),
        processing=DocumentProcessingRepository(session),
        domain_service=domain_service,
    )
    try:
        return service.build_for_domain(domain_id=domain_id, user=user)
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
