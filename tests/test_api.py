import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["INDEX_JOBS_INLINE"] = "true"
Path(".data/test_context_engine.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient  # noqa: E402

from app.domain.models import UserRole  # noqa: E402
from app.main import app  # noqa: E402
from app.storage.db import SessionLocal  # noqa: E402
from app.services.job_service import JobService  # noqa: E402
from app.storage.repositories.jobs import JobRepository  # noqa: E402
from app.storage.repositories.users import UserRepository  # noqa: E402
from app.workers.tasks import run_index_job  # noqa: E402


def _seed_users() -> None:
    with SessionLocal() as session:
        users = UserRepository(session)
        users.create(email="admin@example.com", password="secret", role=UserRole.ADMIN)
        users.create(email="user@example.com", password="secret", role=UserRole.USER)


def _login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_admin_guardrails_and_document_query_flow() -> None:
    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        user_headers = _login(client, "user@example.com")

        blocked = client.get("/admin/ping", headers=user_headers)
        assert blocked.status_code == 403

        upload = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            files={"file": ("manual.txt", b"Installation steps live on page one.", "text/plain")},
        )
        assert upload.status_code == 200
        document_id = upload.json()["document"]["id"]

        documents = client.get("/documents", headers=user_headers)
        assert documents.status_code == 200
        assert documents.json()[0]["id"] == document_id

        retrieve = client.post(
            "/query/retrieve",
            headers=user_headers,
            json={"query": "where are installation steps", "mode": "auto", "top_k": 3},
        )
        assert retrieve.status_code == 200
        body = retrieve.json()
        assert body["mode"] == "navigation"
        assert body["evidence"][0]["source_engine"] == "navigation"

        answer = client.post(
            "/query/answer",
            headers=user_headers,
            json={"query": "where are installation steps", "mode": "hybrid", "top_k": 3},
        )
        assert answer.status_code == 200
        assert "evidence item" in answer.json()["answer"]


def test_index_job_can_be_enqueued_without_running_inline() -> None:
    class FakeQueue:
        def __init__(self) -> None:
            self.enqueued: list[tuple[object, str]] = []

        def enqueue(self, function: object, job_id: str):
            self.enqueued.append((function, job_id))
            return type("QueuedJob", (), {"id": "rq-job-1"})()

    with SessionLocal() as session:
        queue = FakeQueue()
        job_id = JobService(session, queue=queue, run_inline=False).enqueue_index_document(
            document_id="missing-document"
        )
        job = JobRepository(session).get(job_id)

    assert len(queue.enqueued) == 1
    assert queue.enqueued[0][1] == job_id
    assert job.status == "queued"
    assert job.meta["rq_job_id"] == "rq-job-1"


def test_worker_marks_failed_index_job_when_document_is_missing() -> None:
    with SessionLocal() as session:
        job = JobRepository(session).create(kind="index_document", document_id="missing-document")
        job_id = job.id

    run_index_job(job_id)

    with SessionLocal() as session:
        refreshed = JobRepository(session).get(job_id)

    assert refreshed.status == "failed"
    assert "not found" in refreshed.error_message

