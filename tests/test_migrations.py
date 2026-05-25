from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def test_alembic_document_processing_revision_upgrades_existing_baseline(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"
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

    assert "document_sections" in tables
    assert "document_pages" in tables
    assert "document_blocks" in tables
    assert "document_source_chunks" in tables
    assert "document_assets" in tables
    assert "parsed_documents" not in tables
    assert "navigation_indexes" not in tables
    assert "toc_refinement_reports" not in tables


def test_alembic_head_creates_schema_on_fresh_database(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "fresh.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_engine(database_url, future=True)
    tables = set(inspect(engine).get_table_names())

    assert "users" in tables
    assert "documents" in tables
    assert "jobs" in tables
    assert "audit_logs" in tables
    assert "query_logs" in tables
    assert "document_pages" in tables


def test_alembic_document_ingest_revision_renames_legacy_jobs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "jobs.db"
    database_url = f"sqlite:///{database_path}"
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
