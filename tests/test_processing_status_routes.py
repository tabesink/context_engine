import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["INDEX_JOBS_INLINE"] = "true"
Path(".data").mkdir(parents=True, exist_ok=True)

from fastapi.testclient import TestClient

from app.domain.models import UserRole
from app.main import app
from app.schemas.processing_status import (
    DomainProcessingStatusResponse,
    ProcessingStatusPagination,
    ProcessingStatusListResponse,
    ProcessingCounts,
)
from app.services.processing_status_service import ProcessingStatusService
from app.storage.db import SessionLocal, create_db_and_tables
from app.storage.repositories.users import UserRepository


def _seed_users() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        users = UserRepository(session)
        if not users.get_by_email("admin@example.com"):
            users.create(email="admin@example.com", password="secret", role=UserRole.ADMIN)
        if not users.get_by_email("user@example.com"):
            users.create(email="user@example.com", password="secret", role=UserRole.USER)


def _login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_processing_status_routes_auth_and_projection(monkeypatch) -> None:
    _seed_users()

    def fake_domain(self, *, domain_id: str, admin: bool):
        return DomainProcessingStatusResponse(
            domain_id=domain_id,
            state="idle",
            is_busy=False,
            is_stale=False,
            updated_at="2026-05-28T12:00:00Z",
            counts=ProcessingCounts(ready=3),
            documents=[] if not admin else [],
            lightrag=None if not admin else None,
            errors=[],
        )

    monkeypatch.setattr(ProcessingStatusService, "get_domain_status", fake_domain)

    with TestClient(app) as client:
        user_headers = _login(client, "user@example.com")
        admin_headers = _login(client, "admin@example.com")

        user_response = client.get("/lightrag/domains/default/processing-status", headers=user_headers)
        assert user_response.status_code == 200
        assert user_response.json()["counts"]["ready"] == 3

        admin_response = client.get("/admin/lightrag/domains/default/processing-status", headers=admin_headers)
        assert admin_response.status_code == 200

        forbidden = client.get("/admin/lightrag/domains/default/processing-status", headers=user_headers)
        assert forbidden.status_code == 403


def test_processing_status_admin_domain_documents_route(monkeypatch) -> None:
    _seed_users()

    def fake_documents(self, *, domain_id: str, limit: int = 50, offset: int = 0):
        return ProcessingStatusListResponse(
            domain_id=domain_id,
            documents=[],
            status_counts=ProcessingCounts(),
            pagination=ProcessingStatusPagination(limit=limit, offset=offset, returned=0, total=0),
            updated_at="2026-05-28T12:00:00Z",
        )

    monkeypatch.setattr(ProcessingStatusService, "get_admin_domain_documents_status", fake_documents)

    with TestClient(app) as client:
        user_headers = _login(client, "user@example.com")
        admin_headers = _login(client, "admin@example.com")

        admin_response = client.get(
            "/admin/lightrag/domains/default/documents/processing-status?limit=25&offset=0",
            headers=admin_headers,
        )
        assert admin_response.status_code == 200
        assert admin_response.json()["domain_id"] == "default"
        assert admin_response.json()["pagination"]["limit"] == 25
        assert admin_response.json()["pagination"]["offset"] == 0

        forbidden = client.get(
            "/admin/lightrag/domains/default/documents/processing-status",
            headers=user_headers,
        )
        assert forbidden.status_code == 403
