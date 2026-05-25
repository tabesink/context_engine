"""rename lightrag ingest jobs to document_ingest

Revision ID: 0005_document_ingest_job_kind
Revises: 0004_drop_legacy_navigation
Create Date: 2026-05-25 00:00:02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005_document_ingest_job_kind"
down_revision: str | None = "0004_drop_legacy_navigation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if "jobs" not in set(sa.inspect(bind).get_table_names()):
        return
    op.execute(
        sa.text(
            "UPDATE jobs SET kind = :new_kind WHERE kind = :old_kind"
        ).bindparams(new_kind="document_ingest", old_kind="lightrag_ingest_document")
    )


def downgrade() -> None:
    bind = op.get_bind()
    if "jobs" not in set(sa.inspect(bind).get_table_names()):
        return
    op.execute(
        sa.text(
            "UPDATE jobs SET kind = :old_kind WHERE kind = :new_kind"
        ).bindparams(new_kind="document_ingest", old_kind="lightrag_ingest_document")
    )
