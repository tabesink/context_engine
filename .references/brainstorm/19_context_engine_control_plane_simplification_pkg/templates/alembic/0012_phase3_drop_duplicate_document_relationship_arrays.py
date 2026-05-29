"""phase3 drop duplicate document relationship arrays

Revision ID: 0012_phase3_drop_duplicate_document_relationship_arrays
Revises: 0011_phase2_promote_lightrag_domains
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_phase3_drop_duplicate_document_relationship_arrays"
down_revision = "0011_phase2_promote_lightrag_domains"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only run this migration after repository/API code derives these values from canonical relationships.
    op.drop_column("document_sections", "block_ids")
    op.drop_column("document_sections", "child_section_ids")
    op.drop_column("document_blocks", "asset_ids")
    op.drop_column("document_source_chunks", "asset_ids")

    # Intentionally keep document_source_chunks.block_ids unless a document_chunk_blocks join table is added.
    # A source chunk can legitimately span multiple blocks.


def downgrade() -> None:
    json_type = sa.JSON()
    op.add_column("document_source_chunks", sa.Column("asset_ids", json_type, nullable=True))
    op.add_column("document_blocks", sa.Column("asset_ids", json_type, nullable=True))
    op.add_column("document_sections", sa.Column("child_section_ids", json_type, nullable=True))
    op.add_column("document_sections", sa.Column("block_ids", json_type, nullable=True))

    op.execute("UPDATE document_source_chunks SET asset_ids = '[]' WHERE asset_ids IS NULL")
    op.execute("UPDATE document_blocks SET asset_ids = '[]' WHERE asset_ids IS NULL")
    op.execute("UPDATE document_sections SET child_section_ids = '[]' WHERE child_section_ids IS NULL")
    op.execute("UPDATE document_sections SET block_ids = '[]' WHERE block_ids IS NULL")
