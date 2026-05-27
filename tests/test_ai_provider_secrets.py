import os
from datetime import UTC, datetime

os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/test_context_engine.db")
os.environ.setdefault("ENVIRONMENT", "test")

from app.services.ai_model_settings_service import AIModelSettingsService  # noqa: E402
from app.api.routes.lightrag_admin import get_domain_service  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.lightrag_deploy.models import DomainEmbeddingSnapshot, LightRAGDomain  # noqa: E402
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


def test_lightrag_domain_service_reads_stored_provider_secret() -> None:
    _reset_state()
    with SessionLocal() as session:
        crypto = SecretCryptoService.from_settings(get_settings())
        secrets = AIProviderSecretRepository(session, crypto)
        secrets.set_secret(
            secret_name="OPENAI_API_KEY",
            value="sk-test-secret",
            updated_by_user_id="actor",
        )
        domain_service = get_domain_service(session=session)
        domain = LightRAGDomain(
            id="fatigue",
            display_name="Fatigue",
            host_port=9621,
            base_url="http://127.0.0.1:9621",
            host_base_url="http://127.0.0.1:9621",
            container_base_url="http://lightrag_fatigue:9621",
            container_name="context_engine_lightrag_fatigue",
            service_name="lightrag_fatigue",
            status="configured",
            paths={},
            embedding=DomainEmbeddingSnapshot(
                profile_id="openai-text-embedding-3-small",
                provider="openai",
                binding="openai",
                base_url="https://api.openai.com/v1",
                api_key_env_var="OPENAI_API_KEY",
                model="text-embedding-3-small",
                dimensions=1536,
                token_limit=8192,
                send_dimensions=False,
                use_base64=True,
                fingerprint="openai:text-embedding-3-small:1536",
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        resolved = domain_service._provider_secrets_for_domain(domain)

    assert resolved == {"OPENAI_API_KEY": "sk-test-secret"}


def test_profile_validation_message_matches_validate_only_behavior() -> None:
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

        result = service.test_profile("openai-gpt-4o-mini")

    assert result.success is True
    assert result.message == "Configuration validation passed"

