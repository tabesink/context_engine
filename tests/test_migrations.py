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
    assert "document_blocks" in tables
    assert "document_source_chunks" in tables
    assert "document_assets" in tables
    assert "toc_refinement_reports" in tables
