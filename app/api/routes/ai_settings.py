from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.schemas.ai_settings import (
    AIModelProfileResponse,
    AISettingsResponse,
    CreateAIModelProfileRequest,
    ModelProfileTestResult,
    UpdateAIModelProfileRequest,
    UpdateAISettingsDefaultsRequest,
    UpsertProviderSecretRequest,
)
from app.services.ai_model_settings_service import AIModelSettingsService
from app.services.secret_crypto import SecretCryptoService
from app.core.config import get_settings
from app.storage.db import get_session
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository
from app.storage.repositories.ai_provider_secrets import AIProviderSecretRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/admin/ai-settings", tags=["ai-settings"])


def get_ai_settings_service(session: Session = Depends(get_session)) -> AIModelSettingsService:
    crypto = SecretCryptoService.from_settings(get_settings())
    repository = AIModelSettingsRepository(session)
    secrets = AIProviderSecretRepository(session, crypto)
    return AIModelSettingsService(repository, secrets)


@router.get("", response_model=AISettingsResponse)
def get_ai_settings(
    admin: UserRow = Depends(require_admin),
    service: AIModelSettingsService = Depends(get_ai_settings_service),
) -> AISettingsResponse:
    del admin
    return service.get_settings()


@router.put("/defaults", response_model=AISettingsResponse)
def update_defaults(
    request: UpdateAISettingsDefaultsRequest,
    admin: UserRow = Depends(require_admin),
    service: AIModelSettingsService = Depends(get_ai_settings_service),
) -> AISettingsResponse:
    try:
        return service.set_defaults(
            default_llm_profile_id=request.default_llm_profile_id,
            default_embedding_profile_id=request.default_embedding_profile_id,
            updated_by_user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/profiles", response_model=AIModelProfileResponse)
def create_profile(
    request: CreateAIModelProfileRequest,
    admin: UserRow = Depends(require_admin),
    service: AIModelSettingsService = Depends(get_ai_settings_service),
) -> AIModelProfileResponse:
    del admin
    try:
        return service.create_profile(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/profiles/{profile_id}", response_model=AIModelProfileResponse)
def update_profile(
    profile_id: str,
    request: UpdateAIModelProfileRequest,
    admin: UserRow = Depends(require_admin),
    service: AIModelSettingsService = Depends(get_ai_settings_service),
) -> AIModelProfileResponse:
    del admin
    try:
        return service.update_profile(profile_id, request)
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if "does not exist" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/profiles/{profile_id}/test", response_model=ModelProfileTestResult)
def test_profile(
    profile_id: str,
    admin: UserRow = Depends(require_admin),
    service: AIModelSettingsService = Depends(get_ai_settings_service),
) -> ModelProfileTestResult:
    del admin
    try:
        return service.test_profile(profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/provider-secrets/{secret_name}", response_model=AISettingsResponse)
def set_provider_secret(
    secret_name: str,
    request: UpsertProviderSecretRequest,
    admin: UserRow = Depends(require_admin),
    service: AIModelSettingsService = Depends(get_ai_settings_service),
) -> AISettingsResponse:
    try:
        return service.set_provider_secret(
            secret_name=secret_name,
            value=request.value,
            updated_by_user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/provider-secrets/{secret_name}", response_model=AISettingsResponse)
def clear_provider_secret(
    secret_name: str,
    admin: UserRow = Depends(require_admin),
    service: AIModelSettingsService = Depends(get_ai_settings_service),
) -> AISettingsResponse:
    del admin
    try:
        return service.clear_provider_secret(secret_name=secret_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

