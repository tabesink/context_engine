import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/test_context_engine.db")
os.environ.setdefault("ENVIRONMENT", "test")

from app.services.ai_model_settings_service import AIModelSettingsService  # noqa: E402
from app.services.model_profile_resolver import ModelProfileResolver  # noqa: E402
from app.storage.db import SessionLocal, create_db_and_tables  # noqa: E402
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository  # noqa: E402
from app.storage.tables import AIModelProfileRow, AIModelSettingsRow  # noqa: E402


def _reset_state() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        session.query(AIModelSettingsRow).delete()
        session.query(AIModelProfileRow).delete()
        session.commit()


def test_resolver_uses_explicit_embedding_profile() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        service.get_settings()
        resolver = ModelProfileResolver(service)
        profile = resolver.resolve_embedding_profile("openai-text-embedding-3-large")

    assert profile.id == "openai-text-embedding-3-large"
    assert profile.kind == "embedding"


def test_resolver_falls_back_to_default_embedding_profile() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        service.get_settings()
        resolver = ModelProfileResolver(service)
        profile = resolver.resolve_embedding_profile(None)

    assert profile.id == "openai-text-embedding-3-small"


def test_resolver_falls_back_to_default_llm_profile() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        service.get_settings()
        resolver = ModelProfileResolver(service)
        profile = resolver.resolve_llm_profile()

    assert profile.id == "openai-gpt-4o-mini"
    assert profile.kind == "llm"


def test_resolver_uses_explicit_llm_profile() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsService(AIModelSettingsRepository(session))
        service.get_settings()
        resolver = ModelProfileResolver(service)
        profile = resolver.resolve_llm_profile("bedrock-gpt-oss-120b")

    assert profile.id == "bedrock-gpt-oss-120b"
    assert profile.model == "openai.gpt-oss-120b-1:0"

