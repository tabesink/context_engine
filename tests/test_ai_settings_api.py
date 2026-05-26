import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/test_context_engine.db")
os.environ.setdefault("ENVIRONMENT", "test")
Path(".data").mkdir(parents=True, exist_ok=True)

from fastapi.testclient import TestClient  # noqa: E402

from app.domain.models import UserRole  # noqa: E402
from app.main import app  # noqa: E402
from app.storage.db import SessionLocal, create_db_and_tables  # noqa: E402
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository  # noqa: E402
from app.storage.repositories.users import UserRepository  # noqa: E402
from app.storage.tables import AIModelProfileRow, AIModelSettingsRow, AIProviderSecretRow  # noqa: E402


def _reset_state() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        session.query(AIProviderSecretRow).delete()
        session.query(AIModelSettingsRow).delete()
        session.query(AIModelProfileRow).delete()
        users = UserRepository(session)
        if not users.get_by_email("admin@example.com"):
            users.create(email="admin@example.com", password="secret", role=UserRole.ADMIN)
        if not users.get_by_email("user@example.com"):
            users.create(email="user@example.com", password="secret", role=UserRole.USER)
        session.commit()


def _login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": "secret"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_ai_settings_routes_require_admin() -> None:
    _reset_state()
    with TestClient(app) as client:
        headers = _login(client, "user@example.com")
        response = client.get("/admin/ai-settings", headers=headers)
    assert response.status_code == 403


def test_admin_can_list_ai_settings() -> None:
    _reset_state()
    with TestClient(app) as client:
        headers = _login(client, "admin@example.com")
        response = client.get("/admin/ai-settings", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["defaults"]["llm_profile_id"] == "openai-gpt-4o-mini"
    assert body["defaults"]["embedding_profile_id"] == "openai-text-embedding-3-small"
    assert len(body["profiles"]) >= 4


def test_ai_settings_reject_kind_mismatch() -> None:
    _reset_state()
    with TestClient(app) as client:
        headers = _login(client, "admin@example.com")
        response = client.put(
            "/admin/ai-settings/defaults",
            headers=headers,
            json={
                "default_llm_profile_id": "openai-text-embedding-3-small",
                "default_embedding_profile_id": "openai-gpt-4o-mini",
            },
        )
    assert response.status_code == 400


def test_ai_settings_reject_disabled_profile_as_default() -> None:
    _reset_state()
    with SessionLocal() as session:
        service = AIModelSettingsRepository(session)
        row = service.get_profile("openai-text-embedding-3-small")
        if row is None:
            from app.services.ai_model_settings_service import AIModelSettingsService

            AIModelSettingsService(service).get_settings()
            row = service.get_profile("openai-text-embedding-3-small")
        assert row is not None
        row.is_enabled = False
        service.update_profile(row)
    with TestClient(app) as client:
        headers = _login(client, "admin@example.com")
        response = client.put(
            "/admin/ai-settings/defaults",
            headers=headers,
            json={
                "default_llm_profile_id": "openai-gpt-4o-mini",
                "default_embedding_profile_id": "openai-text-embedding-3-small",
            },
        )
    assert response.status_code == 400


def test_admin_can_store_and_clear_provider_secret_without_echoing_value() -> None:
    _reset_state()
    with TestClient(app) as client:
        admin_headers = _login(client, "admin@example.com")
        saved = client.put(
            "/admin/ai-settings/provider-secrets/OPENAI_API_KEY",
            headers=admin_headers,
            json={"value": "sk-test-secret"},
        )
        assert saved.status_code == 200
        saved_body = saved.json()
        assert saved_body["secret_status"]["OPENAI_API_KEY"] == "present"
        assert "sk-test-secret" not in saved.text

        cleared = client.delete(
            "/admin/ai-settings/provider-secrets/OPENAI_API_KEY",
            headers=admin_headers,
        )
        assert cleared.status_code == 200
        assert cleared.json()["secret_status"]["OPENAI_API_KEY"] == "missing"


def test_provider_secret_routes_require_admin() -> None:
    _reset_state()
    with TestClient(app) as client:
        user_headers = _login(client, "user@example.com")
        response = client.put(
            "/admin/ai-settings/provider-secrets/OPENAI_API_KEY",
            headers=user_headers,
            json={"value": "sk-test-secret"},
        )
    assert response.status_code == 403

