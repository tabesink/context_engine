import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["ENVIRONMENT"] = "test"
Path(".data").mkdir(parents=True, exist_ok=True)

from app.schemas.processing_status import ProcessingStatusError
from app.services.processing_status_service import ProcessingStatusService
from app.storage.db import SessionLocal, create_db_and_tables


def test_processing_status_service_local_only_state_busy() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        service = ProcessingStatusService(session)
        service.domain_registry.validate_available = lambda domain_id: None
        service.documents.list_all_by_lightrag_domain = lambda domain_id: []
        service.jobs.list_latest_by_document_ids = lambda document_ids: []
        service._remote_snapshot = lambda domain_id: (None, False, [])
        service._counts = lambda items: type("Counts", (), {
            "queued": 1,
            "indexing": 2,
            "ready": 0,
            "failed": 0,
            "deleted": 0,
            "unknown": 0,
        })()

        response = service.get_domain_status(domain_id="default", admin=False)

    assert response.state == "busy"
    assert response.is_busy is True
    assert response.documents == []


def test_processing_status_service_unreachable_is_stale() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        service = ProcessingStatusService(session)
        service.domain_registry.validate_available = lambda domain_id: None
        service.documents.list_all_by_lightrag_domain = lambda domain_id: []
        service.jobs.list_latest_by_document_ids = lambda document_ids: []
        service._remote_snapshot = lambda domain_id: (
            None,
            True,
            [ProcessingStatusError(code="domain_unreachable", source="lightrag", message="down")],
        )

        response = service.get_domain_status(domain_id="default", admin=True)

    assert response.is_stale is True
    assert response.state == "unreachable"
    assert response.errors[0].code == "domain_unreachable"


def test_processing_status_service_admin_domain_documents_list() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        service = ProcessingStatusService(session)
        service.domain_registry.validate_available = lambda domain_id: None
        service.documents.list_all_by_lightrag_domain = lambda domain_id: []
        service.jobs.list_latest_by_document_ids = lambda document_ids: []

        response = service.get_admin_domain_documents_status(domain_id="default", limit=25, offset=0)

    assert response.domain_id == "default"
    assert response.documents == []
    assert response.status_counts.queued == 0
    assert response.pagination.limit == 25
    assert response.pagination.offset == 0
    assert response.pagination.returned == 0
