"""drop legacy navigation and toc report tables

Revision ID: 0004_drop_legacy_navigation
Revises: 0003_document_pages
Create Date: 2026-05-25 00:00:01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_drop_legacy_navigation"
down_revision: str | None = "0003_document_pages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name in ("parsed_documents", "navigation_indexes", "toc_refinement_reports"):
        if table_name in existing_tables:
            op.drop_table(table_name)


def downgrade() -> None:
    op.create_table(
        "parsed_documents",
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), primary_key=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("pages", sa.JSON(), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
    )
    op.create_table(
        "navigation_indexes",
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("tree", sa.JSON(), nullable=False),
    )
    op.create_table(
        "toc_refinement_reports",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("validation_accuracy", sa.Float(), nullable=True),
        sa.Column("logical_to_physical_offset", sa.Integer(), nullable=True),
        sa.Column("llm_call_count", sa.Integer(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_toc_refinement_reports_document_id", "toc_refinement_reports", ["document_id"])
