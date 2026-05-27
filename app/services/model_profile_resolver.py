from app.services.ai_model_settings_service import AIModelSettingsService
from app.storage.tables import AIModelProfileRow


class ModelProfileResolver:
    def __init__(self, service: AIModelSettingsService):
        self.service = service

    def resolve_embedding_profile(self, embedding_profile_id: str | None = None) -> AIModelProfileRow:
        if embedding_profile_id:
            profile = self.service.get_profile(embedding_profile_id)
            if profile is None:
                raise ValueError(f"Profile '{embedding_profile_id}' does not exist")
            if profile.kind != "embedding":
                raise ValueError(f"Profile '{embedding_profile_id}' is not an embedding profile")
            if not profile.is_enabled:
                raise ValueError(f"Profile '{embedding_profile_id}' is disabled")
            return profile
        _, default_embedding = self.service.resolve_defaults()
        return default_embedding

    def resolve_llm_profile(self, llm_profile_id: str | None = None) -> AIModelProfileRow:
        if llm_profile_id:
            profile = self.service.get_profile(llm_profile_id)
            if profile is None:
                raise ValueError(f"Profile '{llm_profile_id}' does not exist")
            if profile.kind != "llm":
                raise ValueError(f"Profile '{llm_profile_id}' is not an llm profile")
            if not profile.is_enabled:
                raise ValueError(f"Profile '{llm_profile_id}' is disabled")
            return profile
        default_llm, _ = self.service.resolve_defaults()
        return default_llm

    def get_provider_secret_value(self, secret_name: str | None) -> str | None:
        return self.service.get_provider_secret_value(secret_name)

