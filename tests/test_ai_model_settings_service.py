import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/test_context_engine.db")
os.environ.setdefault("ENVIRONMENT", "test")

from app.services.ai_model_settings_service import AIModelSettingsService  # noqa: E402
from app.storage.db import SessionLocal, create_db_and_tables  # noqa: E402
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository  # noqa: E402
from app.storage.tables import AIModelProfileRow, AIModelSettingsRow  # noqa: E402


def _reset_state() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        session.query(AIModelSettingsRow).delete()
        session.query(AIModelProfileRow).delete()
        session.commit()


def test_service_seeds_defaults_and_profiles() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        response = service.get_settings()

    assert response.defaults.llm_profile_id == "openai-gpt-4o-mini"
    assert response.defaults.embedding_profile_id == "openai-text-embedding-3-small"
    assert len(response.profiles) >= 4


def test_service_rejects_wrong_kind_defaults() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        service.get_settings()
        try:
            service.set_defaults(
                default_llm_profile_id="openai-text-embedding-3-small",
                default_embedding_profile_id="openai-gpt-4o-mini",
                updated_by_user_id=None,
            )
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "not a llm profile" in str(exc) or "not a embedding profile" in str(exc)


def test_service_rejects_missing_required_secret() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        service.get_settings()
        try:
            service.set_defaults(
                default_llm_profile_id="openai-gpt-4o-mini",
                default_embedding_profile_id="openai-text-embedding-3-small",
                updated_by_user_id=None,
            )
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "Missing required secret" in str(exc)


def test_service_allows_defaults_when_secret_present(monkeypatch) -> None:
    _reset_state()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        response = service.set_defaults(
            default_llm_profile_id="openai-gpt-4o-mini",
            default_embedding_profile_id="openai-text-embedding-3-small",
            updated_by_user_id="actor",
        )

    assert response.defaults.llm_profile_id == "openai-gpt-4o-mini"
    assert response.secret_status["OPENAI_API_KEY"] == "present"

