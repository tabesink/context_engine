from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.lightrag_deploy.errors import DomainNotFoundError, PermanentDeleteDisabledError
from app.lightrag_deploy.models import (
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainPurgePreview,
    LightRAGDomainPurgeResult,
    LightRAGDomainRemoveResponse,
)
from app.lightrag_deploy.service import LightRAGDomainService
from app.services.ai_model_settings_service import AIModelSettingsService
from app.services.domain_purge_service import DomainPurgeService
from app.services.lightrag_domain_registry import LightRAGDomainRegistry
from app.services.model_profile_resolver import ModelProfileResolver
from app.storage.db import get_session
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository
from app.storage.repositories.logs import LogRepository
from app.storage.repositories.lightrag_domain_lifecycle import LightRAGDomainLifecycleRepository
from app.storage.tables import UserRow

router = APIRouter(tags=["lightrag-domains"])


def get_domain_service(session: Session = Depends(get_session)) -> LightRAGDomainService:
    profile_service = AIModelSettingsService(AIModelSettingsRepository(session))
    return LightRAGDomainService(profile_resolver=ModelProfileResolver(profile_service))


def get_domain_registry() -> LightRAGDomainRegistry:
    return LightRAGDomainRegistry()


def get_domain_purge_service(session: Session = Depends(get_session)) -> DomainPurgeService:
    return DomainPurgeService(session)


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
    lifecycle = LightRAGDomainLifecycleRepository(session)
    lifecycle.set_state(
        domain_id=domain_id,
        state="purging" if permanent else "archiving",
    )
    try:
        result = service.remove(domain_id, permanent=permanent)
    except DomainNotFoundError as exc:
        lifecycle.set_state(domain_id=domain_id, state="failed", error_message=str(exc))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermanentDeleteDisabledError as exc:
        lifecycle.set_state(domain_id=domain_id, state="failed", error_message=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    lifecycle.set_state(
        domain_id=domain_id,
        state="purged" if result.permanent else "archived",
    )
    event = "lightrag.domain.deleted_permanently" if result.permanent else "lightrag.domain.archived"
    LogRepository(session).record_audit(
        actor_id=admin.id,
        event=event,
        target_id=result.id,
        metadata={"domain_id": result.id, "archive_path": result.archive_path},
    )
    return result


@router.post("/admin/lightrag/domains/{domain_id}/purge-preview")
def purge_domain_preview(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    service: DomainPurgeService = Depends(get_domain_purge_service),
) -> LightRAGDomainPurgePreview:
    del admin
    try:
        return service.preview_lightrag_domain_purge(domain_id)
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/admin/lightrag/domains/{domain_id}/purge")
def purge_domain(
    domain_id: str,
    confirm_domain_id: str,
    admin: UserRow = Depends(require_admin),
    service: DomainPurgeService = Depends(get_domain_purge_service),
) -> LightRAGDomainPurgeResult:
    try:
        return service.purge_lightrag_domain(
            domain_id=domain_id,
            actor_id=admin.id,
            confirm_domain_id=confirm_domain_id,
        )
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermanentDeleteDisabledError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/lightrag/domains")
def list_user_domains(
    user: UserRow = Depends(get_current_user),
    registry: LightRAGDomainRegistry = Depends(get_domain_registry),
) -> dict[str, list[dict]]:
    del user
    return {
        "domains": [
            {
                "id": domain.id,
                "display_name": domain.display_name,
                "host_port": domain.host_port,
                "is_healthy": domain.is_healthy,
                "is_default": domain.is_default,
                "status": domain.status,
                "retrieval_defaults": domain.retrieval_defaults,
            }
            for domain in registry.list_domains()
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
        result = operation(domain_id)
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result.status != "succeeded":
        raise HTTPException(
            status_code=502,
            detail={
                "code": "lightrag_domain_operation_failed",
                "domain_id": result.id,
                "operation": result.operation,
                "status": result.status,
                "service_name": result.service_name,
                "message": result.message,
            },
        )
    return result


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
