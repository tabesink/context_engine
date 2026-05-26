import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/test_context_engine.db")
os.environ.setdefault("ENVIRONMENT", "test")

from app.services.ai_model_settings_service import AIModelSettingsService  # noqa: E402
from app.services.secret_crypto import SecretCryptoService  # noqa: E402
from app.storage.db import SessionLocal, create_db_and_tables  # noqa: E402
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository  # noqa: E402
from app.storage.repositories.ai_provider_secrets import AIProviderSecretRepository  # noqa: E402
from app.storage.tables import AIModelProfileRow, AIModelSettingsRow, AIProviderSecretRow  # noqa: E402


def _reset_state() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        session.query(AIProviderSecretRow).delete()
        session.query(AIModelSettingsRow).delete()
        session.query(AIModelProfileRow).delete()
        session.commit()


def test_provider_secret_is_encrypted_at_rest() -> None:
    _reset_state()
    with SessionLocal() as session:
        crypto = SecretCryptoService("test-secret-key")
        repository = AIProviderSecretRepository(session, crypto)

        repository.set_secret(
            secret_name="OPENAI_API_KEY",
            value="sk-test-secret",
            updated_by_user_id="actor",
        )
        row = session.get(AIProviderSecretRow, "OPENAI_API_KEY")

        assert row is not None
        assert row.encrypted_value != "sk-test-secret"
        assert "sk-test-secret" not in row.encrypted_value
        assert repository.get_secret("OPENAI_API_KEY") == "sk-test-secret"


def test_ai_settings_service_uses_stored_secret_for_readiness() -> None:
    _reset_state()
    with SessionLocal() as session:
        crypto = SecretCryptoService("test-secret-key")
        secrets = AIProviderSecretRepository(session, crypto)
        service = AIModelSettingsService(AIModelSettingsRepository(session), secrets)
        service.set_provider_secret(
            secret_name="OPENAI_API_KEY",
            value="sk-test-secret",
            updated_by_user_id="actor",
        )

        response = service.set_defaults(
            default_llm_profile_id="openai-gpt-4o-mini",
            default_embedding_profile_id="openai-text-embedding-3-small",
            updated_by_user_id="actor",
        )

    assert response.secret_status["OPENAI_API_KEY"] == "present"

