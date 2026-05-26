from pydantic import BaseModel, Field

from app.domain.ai_models import ModelProfileKind, ProviderKind


class AIModelProfileResponse(BaseModel):
    id: str
    kind: ModelProfileKind
    provider: ProviderKind
    display_name: str
    model: str
    base_url: str
    api_key_env_var: str | None = None
    api_key_status: str
    binding: str
    dimensions: int | None = None
    token_limit: int | None = None
    send_dimensions: bool = False
    use_base64: bool = True
    is_enabled: bool = True
    is_default: bool = False
    extra: dict = Field(default_factory=dict)


class AISettingsDefaults(BaseModel):
    llm_profile_id: str
    embedding_profile_id: str


class AISettingsResponse(BaseModel):
    defaults: AISettingsDefaults
    profiles: list[AIModelProfileResponse]
    secret_status: dict[str, str]


class UpdateAISettingsDefaultsRequest(BaseModel):
    default_llm_profile_id: str
    default_embedding_profile_id: str


class UpsertProviderSecretRequest(BaseModel):
    value: str = Field(min_length=1, max_length=4096)


class CreateAIModelProfileRequest(BaseModel):
    id: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9][a-z0-9._:-]{1,127}$")
    kind: ModelProfileKind
    provider: ProviderKind
    display_name: str = Field(min_length=2, max_length=255)
    model: str = Field(min_length=1, max_length=255)
    base_url: str = Field(min_length=1, max_length=1024)
    api_key_env_var: str | None = Field(default=None, max_length=128)
    binding: str = Field(min_length=1, max_length=64)
    dimensions: int | None = Field(default=None, ge=1)
    token_limit: int | None = Field(default=None, ge=1)
    send_dimensions: bool = False
    use_base64: bool = True
    is_enabled: bool = True
    extra: dict = Field(default_factory=dict)


class UpdateAIModelProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    model: str | None = Field(default=None, min_length=1, max_length=255)
    base_url: str | None = Field(default=None, min_length=1, max_length=1024)
    api_key_env_var: str | None = Field(default=None, max_length=128)
    binding: str | None = Field(default=None, min_length=1, max_length=64)
    dimensions: int | None = Field(default=None, ge=1)
    token_limit: int | None = Field(default=None, ge=1)
    send_dimensions: bool | None = None
    use_base64: bool | None = None
    is_enabled: bool | None = None
    extra: dict | None = None


class ModelProfileTestResult(BaseModel):
    profile_id: str
    kind: ModelProfileKind
    success: bool
    message: str
    vector_length: int | None = None

