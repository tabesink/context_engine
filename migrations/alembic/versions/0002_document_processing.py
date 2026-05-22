"""add document processing structure and asset tables

Revision ID: 0002_document_processing
Revises: 0001_baseline
Create Date: 2026-05-20 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_document_processing"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_sections",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("parent_section_id", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("block_ids", sa.JSON(), nullable=False),
        sa.Column("child_section_ids", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
    )
    op.create_index("ix_document_sections_document_id", "document_sections", ["document_id"])
    op.create_table(
        "document_blocks",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("section_id", sa.String(length=128), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("bbox", sa.JSON(), nullable=True),
        sa.Column("reading_order", sa.Integer(), nullable=True),
        sa.Column("asset_ids", sa.JSON(), nullable=False),
    )
    op.create_index("ix_document_blocks_document_id", "document_blocks", ["document_id"])
    op.create_index("ix_document_blocks_section_id", "document_blocks", ["section_id"])
    op.create_table(
        "document_source_chunks",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("section_id", sa.String(length=128), nullable=True),
        sa.Column("block_ids", sa.JSON(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("asset_ids", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
    )
    op.create_index("ix_document_source_chunks_document_id", "document_source_chunks", ["document_id"])
    op.create_index("ix_document_source_chunks_section_id", "document_source_chunks", ["section_id"])
    op.create_table(
        "document_assets",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("section_id", sa.String(length=128), nullable=True),
        sa.Column("block_id", sa.String(length=128), nullable=True),
        sa.Column("chunk_id", sa.String(length=128), nullable=True),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("thumbnail_path", sa.String(length=1024), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("nearby_text", sa.Text(), nullable=True),
        sa.Column("bbox", sa.JSON(), nullable=True),
        sa.Column("generated_description", sa.Text(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
    )
    op.create_index("ix_document_assets_document_id", "document_assets", ["document_id"])
    op.create_index("ix_document_assets_section_id", "document_assets", ["section_id"])
    op.create_index("ix_document_assets_chunk_id", "document_assets", ["chunk_id"])
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


def downgrade() -> None:
    op.drop_table("toc_refinement_reports")
    op.drop_table("document_assets")
    op.drop_table("document_source_chunks")
    op.drop_table("document_blocks")
    op.drop_table("document_sections")
