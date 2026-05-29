"""add operation-compatible columns to jobs

Revision ID: 0010_phase1_operation_columns
Revises: 0009_ai_provider_secrets
Create Date: 2026-05-29 12:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0010_phase1_operation_columns"
down_revision: str | None = "0009_ai_provider_secrets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(sa.inspect(bind).get_table_names())


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _add_job_columns() -> None:
    if not _table_exists("jobs"):
        return

    with op.batch_alter_table("jobs") as batch_op:
        if not _column_exists("jobs", "resource_type"):
            batch_op.add_column(sa.Column("resource_type", sa.String(length=32), nullable=True))
        if not _column_exists("jobs", "resource_id"):
            batch_op.add_column(sa.Column("resource_id", sa.String(length=128), nullable=True))
        if not _column_exists("jobs", "requested_by_user_id"):
            batch_op.add_column(
                sa.Column(
                    "requested_by_user_id",
                    sa.String(length=36),
                    sa.ForeignKey("users.id", name="fk_jobs_requested_by_user_id_users"),
                    nullable=True,
                )
            )
        if not _column_exists("jobs", "progress_current"):
            batch_op.add_column(sa.Column("progress_current", sa.Integer(), nullable=True))
        if not _column_exists("jobs", "progress_total"):
            batch_op.add_column(sa.Column("progress_total", sa.Integer(), nullable=True))
        if not _column_exists("jobs", "started_at"):
            batch_op.add_column(sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
        if not _column_exists("jobs", "finished_at"):
            batch_op.add_column(sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))


def _backfill_resource_columns() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE jobs
            SET resource_type = CASE
                WHEN document_id IS NOT NULL THEN 'document'
                ELSE 'system'
            END
            WHERE resource_type IS NULL
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE jobs
            SET resource_id = document_id
            WHERE resource_id IS NULL AND document_id IS NOT NULL
            """
        )
    )


def upgrade() -> None:
    _add_job_columns()
    if _table_exists("jobs"):
        _backfill_resource_columns()


def downgrade() -> None:
    if not _table_exists("jobs"):
        return
    with op.batch_alter_table("jobs") as batch_op:
        if _column_exists("jobs", "finished_at"):
            batch_op.drop_column("finished_at")
        if _column_exists("jobs", "started_at"):
            batch_op.drop_column("started_at")
        if _column_exists("jobs", "progress_total"):
            batch_op.drop_column("progress_total")
        if _column_exists("jobs", "progress_current"):
            batch_op.drop_column("progress_current")
        if _column_exists("jobs", "requested_by_user_id"):
            batch_op.drop_column("requested_by_user_id")
        if _column_exists("jobs", "resource_id"):
            batch_op.drop_column("resource_id")
        if _column_exists("jobs", "resource_type"):
            batch_op.drop_column("resource_type")
