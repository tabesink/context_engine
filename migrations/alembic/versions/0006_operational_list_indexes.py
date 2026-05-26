"""add operational list indexes

Revision ID: 0006_operational_list_indexes
Revises: 0005_document_ingest_job_kind
Create Date: 2026-05-25 16:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006_operational_list_indexes"
down_revision: str | None = "0005_document_ingest_job_kind"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    return any(index["name"] == index_name for index in sa.inspect(bind).get_indexes(table_name))


def _create_index_once(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    _create_index_once("ix_documents_created_at", "documents", ["created_at"])
    _create_index_once("ix_jobs_created_at", "jobs", ["created_at"])
    _create_index_once("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    _create_index_once("ix_query_logs_created_at", "query_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_query_logs_created_at", table_name="query_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_index("ix_documents_created_at", table_name="documents")
