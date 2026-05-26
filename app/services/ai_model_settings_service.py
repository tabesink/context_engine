import os
from datetime import UTC, datetime

from app.domain.ai_models import ModelProfileKind, ProviderKind
from app.schemas.ai_settings import (
    AIModelProfileResponse,
    AISettingsDefaults,
    AISettingsResponse,
    CreateAIModelProfileRequest,
    ModelProfileTestResult,
    UpdateAIModelProfileRequest,
)
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository
from app.storage.repositories.ai_provider_secrets import AIProviderSecretRepository
from app.storage.tables import AIModelProfileRow


class AIModelSettingsService:
    def __init__(
        self,
        repository: AIModelSettingsRepository,
        secret_repository: AIProviderSecretRepository | None = None,
    ):
        self.repository = repository
        self.secret_repository = secret_repository

    def get_settings(self) -> AISettingsResponse:
        self.ensure_seeded()
        settings = self.repository.get_settings()
        if settings is None:
            raise ValueError("AI settings are not configured")

        profiles = self.repository.list_profiles()
        defaults = AISettingsDefaults(
            llm_profile_id=settings.default_llm_profile_id,
            embedding_profile_id=settings.default_embedding_profile_id,
        )
        return AISettingsResponse(
            defaults=defaults,
            profiles=[
                self._to_response(
                    profile,
                    is_default=(
                        profile.id in {settings.default_llm_profile_id, settings.default_embedding_profile_id}
                    ),
                )
                for profile in profiles
            ],
            secret_status=self._secret_status(profiles),
        )

    def set_defaults(
        self,
        *,
        default_llm_profile_id: str,
        default_embedding_profile_id: str,
        updated_by_user_id: str | None = None,
    ) -> AISettingsResponse:
        self.ensure_seeded()
        llm = self._require_enabled(default_llm_profile_id, expected_kind=ModelProfileKind.LLM)
        embedding = self._require_enabled(
            default_embedding_profile_id, expected_kind=ModelProfileKind.EMBEDDING
        )
        self._validate_secret(llm)
        self._validate_secret(embedding)
        self.repository.set_defaults(
            llm_profile_id=llm.id,
            embedding_profile_id=embedding.id,
            updated_by_user_id=updated_by_user_id,
        )
        return self.get_settings()

    def create_profile(self, request: CreateAIModelProfileRequest) -> AIModelProfileResponse:
        existing = self.repository.get_profile(request.id)
        if existing:
            raise ValueError(f"Profile '{request.id}' already exists")
        if request.kind == ModelProfileKind.EMBEDDING and request.dimensions is None:
            raise ValueError("Embedding profiles must define dimensions")
        row = AIModelProfileRow(
            id=request.id,
            kind=request.kind.value,
            provider=request.provider.value,
            display_name=request.display_name,
            model=request.model,
            base_url=request.base_url,
            api_key_env_var=request.api_key_env_var,
            binding=request.binding,
            dimensions=request.dimensions,
            token_limit=request.token_limit,
            send_dimensions=request.send_dimensions,
            use_base64=request.use_base64,
            is_enabled=request.is_enabled,
            extra=request.extra,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        created = self.repository.create_profile(row)
        return self._to_response(created, is_default=False)

    def update_profile(self, profile_id: str, request: UpdateAIModelProfileRequest) -> AIModelProfileResponse:
        profile = self.repository.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile '{profile_id}' does not exist")
        patch = request.model_dump(exclude_unset=True)
        for key, value in patch.items():
            setattr(profile, key, value)
        updated = self.repository.update_profile(profile)
        settings = self.repository.get_settings()
        is_default = bool(
            settings
            and updated.id in {settings.default_llm_profile_id, settings.default_embedding_profile_id}
        )
        return self._to_response(updated, is_default=is_default)

    def test_profile(self, profile_id: str) -> ModelProfileTestResult:
        profile = self.repository.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile '{profile_id}' does not exist")
        try:
            self._validate_secret(profile)
        except ValueError as exc:
            return ModelProfileTestResult(
                profile_id=profile.id,
                kind=ModelProfileKind(profile.kind),
                success=False,
                message=str(exc),
            )
        vector_length = profile.dimensions if profile.kind == ModelProfileKind.EMBEDDING.value else None
        return ModelProfileTestResult(
            profile_id=profile.id,
            kind=ModelProfileKind(profile.kind),
            success=True,
            message="Connection test passed",
            vector_length=vector_length,
        )

    def set_provider_secret(
        self,
        *,
        secret_name: str,
        value: str,
        updated_by_user_id: str | None,
    ) -> AISettingsResponse:
        if self.secret_repository is None:
            raise ValueError("Provider secret storage is not configured")
        normalized = self._normalize_secret_name(secret_name)
        self.secret_repository.set_secret(
            secret_name=normalized,
            value=value,
            updated_by_user_id=updated_by_user_id,
        )
        return self.get_settings()

    def clear_provider_secret(self, *, secret_name: str) -> AISettingsResponse:
        if self.secret_repository is None:
            raise ValueError("Provider secret storage is not configured")
        self.secret_repository.clear_secret(self._normalize_secret_name(secret_name))
        return self.get_settings()

    def get_provider_secret_value(self, secret_name: str | None) -> str | None:
        if not secret_name:
            return None
        normalized = self._normalize_secret_name(secret_name)
        if self.secret_repository is not None:
            stored = self.secret_repository.get_secret(normalized)
            if stored:
                return stored
        return os.getenv(normalized)

    def get_profile(self, profile_id: str) -> AIModelProfileRow | None:
        self.ensure_seeded()
        return self.repository.get_profile(profile_id)

    def resolve_defaults(self) -> tuple[AIModelProfileRow, AIModelProfileRow]:
        self.ensure_seeded()
        settings = self.repository.get_settings()
        if settings is None:
            raise ValueError("AI settings are not configured")
        llm = self._require_enabled(settings.default_llm_profile_id, expected_kind=ModelProfileKind.LLM)
        embedding = self._require_enabled(
            settings.default_embedding_profile_id, expected_kind=ModelProfileKind.EMBEDDING
        )
        return llm, embedding

    def ensure_seeded(self) -> None:
        if self.repository.list_profiles():
            if self.repository.get_settings() is not None:
                return
        defaults = [
            AIModelProfileRow(
                id="openai-gpt-4o-mini",
                kind=ModelProfileKind.LLM.value,
                provider=ProviderKind.OPENAI.value,
                display_name="OpenAI gpt-4o-mini",
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                api_key_env_var="OPENAI_API_KEY",
                binding="openai",
                is_enabled=True,
                extra={},
            ),
            AIModelProfileRow(
                id="bedrock-gpt-oss-120b",
                kind=ModelProfileKind.LLM.value,
                provider=ProviderKind.BEDROCK_OPENAI.value,
                display_name="Bedrock GPT OSS 120B",
                model="openai.gpt-oss-120b-1:0",
                base_url="https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1",
                api_key_env_var="AWS_BEARER_TOKEN_BEDROCK",
                binding="openai",
                is_enabled=True,
                extra={},
            ),
            AIModelProfileRow(
                id="openai-text-embedding-3-small",
                kind=ModelProfileKind.EMBEDDING.value,
                provider=ProviderKind.OPENAI.value,
                display_name="OpenAI text-embedding-3-small",
                model="text-embedding-3-small",
                base_url="https://api.openai.com/v1",
                api_key_env_var="OPENAI_API_KEY",
                binding="openai",
                dimensions=1536,
                token_limit=8192,
                is_enabled=True,
                extra={},
            ),
            AIModelProfileRow(
                id="openai-text-embedding-3-large",
                kind=ModelProfileKind.EMBEDDING.value,
                provider=ProviderKind.OPENAI.value,
                display_name="OpenAI text-embedding-3-large",
                model="text-embedding-3-large",
                base_url="https://api.openai.com/v1",
                api_key_env_var="OPENAI_API_KEY",
                binding="openai",
                dimensions=3072,
                token_limit=8192,
                is_enabled=True,
                extra={},
            ),
        ]
        for profile in defaults:
            if self.repository.get_profile(profile.id) is None:
                self.repository.create_profile(profile)
        self.repository.set_defaults(
            llm_profile_id="openai-gpt-4o-mini",
            embedding_profile_id="openai-text-embedding-3-small",
            updated_by_user_id=None,
        )

    def _require_enabled(
        self, profile_id: str, *, expected_kind: ModelProfileKind
    ) -> AIModelProfileRow:
        profile = self.repository.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile '{profile_id}' does not exist")
        if profile.kind != expected_kind.value:
            raise ValueError(f"Profile '{profile_id}' is not a {expected_kind.value} profile")
        if not profile.is_enabled:
            raise ValueError(f"Profile '{profile_id}' is disabled")
        return profile

    def _validate_secret(self, profile: AIModelProfileRow) -> None:
        env_var = (profile.api_key_env_var or "").strip()
        if profile.provider == ProviderKind.OLLAMA.value:
            return
        if not env_var:
            raise ValueError(f"Profile '{profile.id}' requires an API key env var")
        if not self.get_provider_secret_value(env_var):
            raise ValueError(f"Missing required secret: {env_var}")

    def _api_key_status(self, profile: AIModelProfileRow) -> str:
        if profile.provider == ProviderKind.OLLAMA.value:
            return "not_required"
        env_var = (profile.api_key_env_var or "").strip()
        if not env_var:
            return "missing"
        return "present" if self.get_provider_secret_value(env_var) else "missing"

    def _secret_status(self, profiles: list[AIModelProfileRow]) -> dict[str, str]:
        status: dict[str, str] = {}
        for profile in profiles:
            env_var = (profile.api_key_env_var or "").strip()
            if not env_var:
                continue
            status[env_var] = "present" if self.get_provider_secret_value(env_var) else "missing"
        return status

    def _normalize_secret_name(self, secret_name: str) -> str:
        normalized = secret_name.strip().upper()
        if not normalized:
            raise ValueError("Secret name is required")
        return normalized

    def _to_response(self, profile: AIModelProfileRow, *, is_default: bool) -> AIModelProfileResponse:
        return AIModelProfileResponse(
            id=profile.id,
            kind=ModelProfileKind(profile.kind),
            provider=ProviderKind(profile.provider),
            display_name=profile.display_name,
            model=profile.model,
            base_url=profile.base_url,
            api_key_env_var=profile.api_key_env_var,
            api_key_status=self._api_key_status(profile),
            binding=profile.binding,
            dimensions=profile.dimensions,
            token_limit=profile.token_limit,
            send_dimensions=profile.send_dimensions,
            use_base64=profile.use_base64,
            is_enabled=profile.is_enabled,
            is_default=is_default,
            extra=profile.extra or {},
        )

