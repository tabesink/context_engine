"""add document pages table

Revision ID: 0003_document_pages
Revises: 0002_document_processing
Create Date: 2026-05-25 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_document_pages"
down_revision: str | None = "0002_document_processing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "document_pages" not in existing_tables:
        op.create_table(
            "document_pages",
            sa.Column("id", sa.String(length=128), primary_key=True),
            sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
            sa.Column("page_number", sa.Integer(), nullable=False),
            sa.Column("width", sa.Float(), nullable=True),
            sa.Column("height", sa.Float(), nullable=True),
            sa.Column("text", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False),
        )
        existing_tables.add("document_pages")
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("document_pages")} if "document_pages" in existing_tables else set()
    if "ix_document_pages_document_id" not in existing_indexes:
        op.create_index("ix_document_pages_document_id", "document_pages", ["document_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if "document_pages" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("document_pages")
