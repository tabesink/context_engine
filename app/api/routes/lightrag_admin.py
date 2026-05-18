from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.lightrag_deploy.errors import DomainNotFoundError, PermanentDeleteDisabledError
from app.lightrag_deploy.models import (
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainRemoveResponse,
)
from app.lightrag_deploy.service import LightRAGDomainService
from app.storage.db import get_session
from app.storage.repositories.logs import LogRepository
from app.storage.tables import UserRow

router = APIRouter(tags=["lightrag-domains"])


def get_domain_service() -> LightRAGDomainService:
    return LightRAGDomainService()


@router.get("/admin/lightrag/domains")
def list_admin_domains(
    admin: UserRow = Depends(require_admin),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> dict[str, list[LightRAGDomain]]:
    del admin
    _ensure_deploy_enabled(service)
    return {"domains": service.list_domains()}


@router.post("/admin/lightrag/domains")
def create_domain(
    request: LightRAGDomainCreateRequest,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomain:
    _ensure_deploy_enabled(service)
    try:
        domain = service.create_domain(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(session, admin, "lightrag.domain.created", domain)
    return domain


@router.get("/admin/lightrag/domains/{domain_id}")
def show_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomain:
    del admin
    _ensure_deploy_enabled(service)
    return _domain_or_404(service, domain_id)


@router.post("/admin/lightrag/domains/{domain_id}/up")
def up_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainOperationResult:
    _ensure_deploy_enabled(service)
    result = _operation_or_404(service.up, domain_id)
    _audit(session, admin, "lightrag.domain.started", service.get_domain(domain_id))
    return result


@router.post("/admin/lightrag/domains/{domain_id}/down")
def down_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainOperationResult:
    _ensure_deploy_enabled(service)
    result = _operation_or_404(service.down, domain_id)
    _audit(session, admin, "lightrag.domain.stopped", service.get_domain(domain_id))
    return result


@router.post("/admin/lightrag/domains/{domain_id}/recreate")
def recreate_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainOperationResult:
    _ensure_deploy_enabled(service)
    result = _operation_or_404(service.recreate, domain_id)
    _audit(session, admin, "lightrag.domain.recreated", service.get_domain(domain_id))
    return result


@router.post("/admin/lightrag/domains/{domain_id}/regenerate")
def regenerate_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> dict[str, str]:
    _ensure_deploy_enabled(service)
    _domain_or_404(service, domain_id)
    service.regenerate(domain_id)
    _audit(session, admin, "lightrag.domain.regenerated", service.get_domain(domain_id))
    return {"status": "ok"}


@router.delete("/admin/lightrag/domains/{domain_id}")
def remove_domain(
    domain_id: str,
    permanent: bool = False,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainRemoveResponse:
    _ensure_deploy_enabled(service)
    try:
        result = service.remove(domain_id, permanent=permanent)
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermanentDeleteDisabledError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    event = "lightrag.domain.deleted_permanently" if result.permanent else "lightrag.domain.archived"
    LogRepository(session).record_audit(
        actor_id=admin.id,
        event=event,
        target_id=result.id,
        metadata={"domain_id": result.id, "archive_path": result.archive_path},
    )
    return result


@router.get("/lightrag/domains")
def list_user_domains(
    user: UserRow = Depends(get_current_user),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> dict[str, list[dict]]:
    del user
    return {
        "domains": [
            {
                "id": domain.id,
                "display_name": domain.display_name,
                "is_healthy": domain.is_healthy,
                "is_default": domain.is_default,
            }
            for domain in service.list_domains()
        ]
    }


def _ensure_deploy_enabled(service: LightRAGDomainService) -> None:
    if not service.settings.enabled:
        raise HTTPException(status_code=400, detail="LightRAG deployment is disabled")


def _domain_or_404(service: LightRAGDomainService, domain_id: str) -> LightRAGDomain:
    try:
        return service.get_domain(domain_id)
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _operation_or_404(operation, domain_id: str) -> LightRAGDomainOperationResult:
    try:
        return operation(domain_id)
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _audit(session: Session, admin: UserRow, event: str, domain: LightRAGDomain) -> None:
    LogRepository(session).record_audit(
        actor_id=admin.id,
        event=event,
        target_id=domain.id,
        metadata={
            "domain_id": domain.id,
            "host_port": domain.host_port,
            "service_name": domain.service_name,
        },
    )
