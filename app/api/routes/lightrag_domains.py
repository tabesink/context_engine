from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.api.routes import lightrag_admin
from app.core.errors import not_found
from app.lightrag_deploy.models import (
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainRemoveResponse,
)
from app.storage.db import get_session
from app.storage.repositories.lightrag_domains import LightRAGDomainRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/admin/lightrag-domains", tags=["lightrag-domains"])


def _domain_payload(row) -> dict:
    return {
        "id": row.id,
        "display_name": row.display_name,
        "state": row.state,
        "health_status": row.health_status,
        "error_message": row.error_message,
        "metadata": row.meta,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


@router.get("")
def list_lightrag_domains(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> dict[str, list[dict]]:
    del admin
    rows = LightRAGDomainRepository(session).list(limit=limit, offset=offset)
    return {"domains": [_domain_payload(row) for row in rows]}


@router.get("/{domain_id}")
def get_lightrag_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> dict:
    del admin
    row = LightRAGDomainRepository(session).get(domain_id)
    if not row:
        raise not_found("LightRAG domain not found")
    return _domain_payload(row)


@router.post("")
def create_lightrag_domain(
    request: LightRAGDomainCreateRequest,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service=Depends(lightrag_admin.get_domain_service),
) -> LightRAGDomain:
    return lightrag_admin.create_domain(request, admin=admin, session=session, service=service)


@router.post("/{domain_id}/start")
def start_lightrag_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service=Depends(lightrag_admin.get_domain_service),
) -> LightRAGDomainOperationResult:
    return lightrag_admin.up_domain(domain_id, admin=admin, session=session, service=service)


@router.post("/{domain_id}/stop")
def stop_lightrag_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service=Depends(lightrag_admin.get_domain_service),
) -> LightRAGDomainOperationResult:
    return lightrag_admin.down_domain(domain_id, admin=admin, session=session, service=service)


@router.delete("/{domain_id}")
def delete_lightrag_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service=Depends(lightrag_admin.get_domain_service),
) -> LightRAGDomainRemoveResponse:
    return lightrag_admin.remove_domain(domain_id, admin=admin, session=session, service=service)
