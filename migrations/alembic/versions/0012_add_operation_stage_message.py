"""add operation stage and message columns

Revision ID: 0012_operation_stage_message
Revises: 0011_phase2_lightrag_domains
Create Date: 2026-05-29 15:55:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0012_operation_stage_message"
down_revision: str | None = "0011_phase2_lightrag_domains"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(sa.inspect(bind).get_table_names())


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _add_stage_message_columns() -> None:
    if not _table_exists("jobs"):
        return
    with op.batch_alter_table("jobs") as batch_op:
        if not _column_exists("jobs", "stage"):
            batch_op.add_column(sa.Column("stage", sa.String(length=64), nullable=True))
        if not _column_exists("jobs", "message"):
            batch_op.add_column(sa.Column("message", sa.Text(), nullable=True))


def _backfill_stage_message() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE jobs
            SET stage = CASE status
                WHEN 'queued' THEN 'queued'
                WHEN 'running' THEN 'indexing_lightrag'
                WHEN 'succeeded' THEN 'complete'
                WHEN 'failed' THEN 'failed'
                WHEN 'canceled' THEN 'canceled'
                ELSE status
            END
            WHERE stage IS NULL
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE jobs
            SET message = CASE status
                WHEN 'queued' THEN 'Queued for processing'
                WHEN 'running' THEN 'Processing'
                WHEN 'succeeded' THEN 'Complete'
                WHEN 'failed' THEN COALESCE(error_message, 'Failed')
                WHEN 'canceled' THEN 'Canceled'
                ELSE NULL
            END
            WHERE message IS NULL
            """
        )
    )


def upgrade() -> None:
    _add_stage_message_columns()
    if _table_exists("jobs"):
        _backfill_stage_message()


def downgrade() -> None:
    if not _table_exists("jobs"):
        return
    with op.batch_alter_table("jobs") as batch_op:
        if _column_exists("jobs", "message"):
            batch_op.drop_column("message")
        if _column_exists("jobs", "stage"):
            batch_op.drop_column("stage")
