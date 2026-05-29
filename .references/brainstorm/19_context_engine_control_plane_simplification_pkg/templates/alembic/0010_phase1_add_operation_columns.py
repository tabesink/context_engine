"""phase1 add operation-compatible columns to jobs

Revision ID: 0010_phase1_add_operation_columns
Revises: <PUT_CURRENT_HEAD_REVISION_HERE>
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_phase1_add_operation_columns"
down_revision = "<PUT_CURRENT_HEAD_REVISION_HERE>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("resource_type", sa.String(length=32), nullable=True))
    op.add_column("jobs", sa.Column("resource_id", sa.String(length=128), nullable=True))
    op.add_column("jobs", sa.Column("requested_by_user_id", sa.String(length=36), nullable=True))
    op.add_column("jobs", sa.Column("progress_current", sa.Integer(), nullable=True))
    op.add_column("jobs", sa.Column("progress_total", sa.Integer(), nullable=True))
    op.add_column("jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_jobs_resource", "jobs", ["resource_type", "resource_id"])
    op.create_index("ix_jobs_status_resource", "jobs", ["status", "resource_type", "resource_id"])
    op.create_foreign_key(
        "fk_jobs_requested_by_user_id_users",
        "jobs",
        "users",
        ["requested_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill existing document jobs into the generic operation resource shape.
    op.execute("""
        UPDATE jobs
        SET resource_type = 'document', resource_id = document_id
        WHERE document_id IS NOT NULL AND resource_type IS NULL
    """)

    op.execute("""
        UPDATE jobs
        SET resource_type = 'system'
        WHERE document_id IS NULL AND resource_type IS NULL
    """)


def downgrade() -> None:
    op.drop_constraint("fk_jobs_requested_by_user_id_users", "jobs", type_="foreignkey")
    op.drop_index("ix_jobs_status_resource", table_name="jobs")
    op.drop_index("ix_jobs_resource", table_name="jobs")
    op.drop_column("jobs", "finished_at")
    op.drop_column("jobs", "started_at")
    op.drop_column("jobs", "progress_total")
    op.drop_column("jobs", "progress_current")
    op.drop_column("jobs", "requested_by_user_id")
    op.drop_column("jobs", "resource_id")
    op.drop_column("jobs", "resource_type")
