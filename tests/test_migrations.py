from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def test_alembic_revision_ids_fit_default_version_table() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    for revision in script.walk_revisions():
        assert len(revision.revision) <= 32


def test_alembic_document_processing_revision_upgrades_existing_baseline(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    engine = create_engine(database_url, future=True)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE documents (
                    id VARCHAR(36) PRIMARY KEY,
                    owner_id VARCHAR(36),
                    filename VARCHAR(512) NOT NULL,
                    content_type VARCHAR(255) NOT NULL,
                    storage_path VARCHAR(1024) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    active_index_version INTEGER NOT NULL,
                    error_message TEXT,
                    metadata JSON NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    tables = set(inspect(engine).get_table_names())
    columns = {column["name"] for column in inspect(engine).get_columns("documents")}

    assert "document_sections" in tables
    assert "document_pages" in tables
    assert "document_blocks" in tables
    assert "document_source_chunks" in tables
    assert "document_assets" in tables
    assert "parsed_documents" not in tables
    assert "navigation_indexes" not in tables
    assert "toc_refinement_reports" not in tables
    assert "lightrag_domain_lifecycle" in tables
    assert "lightrag_domain_id" in columns


def test_alembic_head_creates_schema_on_fresh_database(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "fresh.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    columns = {column["name"] for column in inspector.get_columns("documents")}

    assert "users" in tables
    assert "documents" in tables
    assert "jobs" in tables
    assert "audit_logs" in tables
    assert "query_logs" in tables
    assert "ai_model_profiles" in tables
    assert "ai_model_settings" in tables
    assert "ai_provider_secrets" in tables
    assert "document_pages" in tables
    assert "lightrag_domain_lifecycle" in tables
    assert "lightrag_domain_id" in columns


def test_alembic_document_ingest_revision_renames_legacy_jobs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "jobs.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    engine = create_engine(database_url, future=True)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE documents (
                    id VARCHAR(36) PRIMARY KEY,
                    owner_id VARCHAR(36),
                    filename VARCHAR(512) NOT NULL,
                    content_type VARCHAR(255) NOT NULL,
                    storage_path VARCHAR(1024) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    active_index_version INTEGER NOT NULL,
                    error_message TEXT,
                    metadata JSON NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE TABLE jobs (
                    id VARCHAR(36) PRIMARY KEY,
                    kind VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    document_id VARCHAR(36),
                    error_message TEXT,
                    metadata JSON NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO jobs (
                    id, kind, status, document_id, error_message, metadata, created_at, updated_at
                )
                VALUES (
                    'job-1', 'lightrag_ingest_document', 'queued', NULL, NULL, '{}',
                    '2026-05-25 00:00:00', '2026-05-25 00:00:00'
                )
                """
            )
        )

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    with engine.connect() as connection:
        kind = connection.execute(sa.text("SELECT kind FROM jobs WHERE id = 'job-1'")).scalar_one()

    assert kind == "document_ingest"


def test_alembic_head_adds_operation_compatible_job_columns_with_backfill(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "operation_jobs.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    engine = create_engine(database_url, future=True)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE documents (
                    id VARCHAR(36) PRIMARY KEY,
                    owner_id VARCHAR(36),
                    filename VARCHAR(512) NOT NULL,
                    content_type VARCHAR(255) NOT NULL,
                    storage_path VARCHAR(1024) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    active_index_version INTEGER NOT NULL,
                    error_message TEXT,
                    metadata JSON NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE TABLE jobs (
                    id VARCHAR(36) PRIMARY KEY,
                    kind VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    document_id VARCHAR(36),
                    error_message TEXT,
                    metadata JSON NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO documents (
                    id, owner_id, filename, content_type, storage_path, status, active_index_version,
                    error_message, metadata, created_at, updated_at
                )
                VALUES (
                    'doc-1', NULL, 'ops.txt', 'text/plain', '/tmp/ops.txt', 'uploaded', 0,
                    NULL, '{}', '2026-05-25 00:00:00', '2026-05-25 00:00:00'
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO jobs (
                    id, kind, status, document_id, error_message, metadata, created_at, updated_at
                )
                VALUES
                    (
                        'job-doc', 'document_ingest', 'queued', 'doc-1', NULL, '{}',
                        '2026-05-25 00:00:00', '2026-05-25 00:00:00'
                    ),
                    (
                        'job-sys', 'document_ingest', 'queued', NULL, NULL, '{}',
                        '2026-05-25 00:00:00', '2026-05-25 00:00:00'
                    )
                """
            )
        )

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("jobs")}
    assert "resource_type" in columns
    assert "resource_id" in columns
    assert "requested_by_user_id" in columns
    assert "progress_current" in columns
    assert "progress_total" in columns
    assert "started_at" in columns
    assert "finished_at" in columns

    with engine.connect() as connection:
        backfilled_rows = connection.execute(
            sa.text(
                """
                SELECT id, resource_type, resource_id
                FROM jobs
                ORDER BY id ASC
                """
            )
        ).all()

    assert backfilled_rows == [
        ("job-doc", "document", "doc-1"),
        ("job-sys", "system", None),
    ]


def test_alembic_head_promotes_lightrag_domains_table_with_lifecycle_backfill(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "lightrag_domains.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    engine = create_engine(database_url, future=True)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE lightrag_domain_lifecycle (
                    domain_id VARCHAR(64) PRIMARY KEY,
                    state VARCHAR(32) NOT NULL,
                    error_message TEXT,
                    metadata JSON NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO lightrag_domain_lifecycle (
                    domain_id, state, error_message, metadata, created_at, updated_at
                ) VALUES (
                    'fatigue', 'active', NULL, '{"display_name": "Fatigue"}',
                    '2026-05-25 00:00:00', '2026-05-25 00:00:00'
                )
                """
            )
        )

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "lightrag_domains" in tables

    columns = {column["name"] for column in inspector.get_columns("lightrag_domains")}
    assert {"id", "display_name", "state", "health_status", "metadata", "created_at", "updated_at"} <= columns

    with engine.connect() as connection:
        row = connection.execute(
            sa.text(
                """
                SELECT id, display_name, state
                FROM lightrag_domains
                WHERE id = 'fatigue'
                """
            )
        ).one()

    assert row == ("fatigue", "Fatigue", "active")
