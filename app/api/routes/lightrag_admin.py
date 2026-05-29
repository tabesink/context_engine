from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.lightrag_deploy.errors import DomainNotFoundError
from app.lightrag_deploy.models import (
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainRemoveResponse,
)
from app.lightrag_deploy.service import LightRAGDomainService
from app.services.ai_model_settings_service import AIModelSettingsService
from app.services.lightrag_domain_registry import LightRAGDomainRegistry
from app.services.model_profile_resolver import ModelProfileResolver
from app.services.secret_crypto import SecretCryptoService
from app.core.config import get_settings
from app.storage.db import get_session
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository
from app.storage.repositories.ai_provider_secrets import AIProviderSecretRepository
from app.storage.repositories.lightrag_domains import LightRAGDomainRepository
from app.storage.repositories.logs import LogRepository
from app.storage.repositories.lightrag_domain_lifecycle import LightRAGDomainLifecycleRepository
from app.storage.tables import UserRow

router = APIRouter(tags=["lightrag-domains"])


def get_domain_service(session: Session = Depends(get_session)) -> LightRAGDomainService:
    crypto = SecretCryptoService.from_settings(get_settings())
    profile_service = AIModelSettingsService(
        AIModelSettingsRepository(session),
        AIProviderSecretRepository(session, crypto),
    )
    return LightRAGDomainService(profile_resolver=ModelProfileResolver(profile_service))


def get_domain_registry() -> LightRAGDomainRegistry:
    return LightRAGDomainRegistry()


def list_admin_domains(
    admin: UserRow = Depends(require_admin),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> dict[str, list[LightRAGDomain]]:
    del admin
    _ensure_deploy_enabled(service)
    return {"domains": service.list_domains()}


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
    LightRAGDomainRepository(session).upsert(
        domain_id=domain.id,
        display_name=domain.display_name,
        state=domain.status or "configured",
        health_status="healthy" if domain.is_healthy else None,
        metadata={"host_port": domain.host_port, "service_name": domain.service_name},
    )
    _audit(session, admin, "lightrag.domain.created", domain)
    return domain


def show_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomain:
    del admin
    _ensure_deploy_enabled(service)
    return _domain_or_404(service, domain_id)


def up_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainOperationResult:
    _ensure_deploy_enabled(service)
    result = _operation_or_404(service.up, domain_id)
    domain = service.get_domain(domain_id)
    LightRAGDomainRepository(session).upsert(
        domain_id=domain.id,
        display_name=domain.display_name,
        state="running" if result.status == "succeeded" else "failed",
        health_status="healthy" if domain.is_healthy else "unhealthy",
        error_message=None if result.status == "succeeded" else (result.message or "startup_failed"),
        metadata={"host_port": domain.host_port, "service_name": domain.service_name},
    )
    _audit(session, admin, "lightrag.domain.started", domain)
    return result


def down_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainOperationResult:
    _ensure_deploy_enabled(service)
    result = _operation_or_404(service.down, domain_id)
    domain = service.get_domain(domain_id)
    LightRAGDomainRepository(session).upsert(
        domain_id=domain.id,
        display_name=domain.display_name,
        state="stopped" if result.status == "succeeded" else "failed",
        health_status="unhealthy" if result.status == "succeeded" else "unhealthy",
        error_message=None if result.status == "succeeded" else (result.message or "shutdown_failed"),
        metadata={"host_port": domain.host_port, "service_name": domain.service_name},
    )
    _audit(session, admin, "lightrag.domain.stopped", domain)
    return result


def remove_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainRemoveResponse:
    _ensure_deploy_enabled(service)
    lifecycle = LightRAGDomainLifecycleRepository(session)
    domains = LightRAGDomainRepository(session)
    lifecycle.set_state(
        domain_id=domain_id,
        state="archiving",
    )
    domains.upsert(domain_id=domain_id, state="archiving")
    try:
        result = service.remove(domain_id)
    except DomainNotFoundError as exc:
        lifecycle.set_state(domain_id=domain_id, state="failed", error_message=str(exc))
        domains.upsert(domain_id=domain_id, state="failed", error_message=str(exc))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    lifecycle.set_state(
        domain_id=domain_id,
        state="archived",
    )
    domains.upsert(
        domain_id=result.id,
        display_name=result.id,
        state="deleted",
        health_status="unhealthy",
        metadata={"archive_path": result.archive_path, "archived": result.archived},
    )
    LogRepository(session).record_audit(
        actor_id=admin.id,
        event="lightrag.domain.archived",
        target_id=result.id,
        metadata={"domain_id": result.id, "archive_path": result.archive_path},
    )
    return result


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
