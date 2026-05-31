"""add upload workflow operation fields to jobs

Revision ID: 0016_upload_workflow_operation_fields
Revises: <PUT_CURRENT_HEAD_REVISION_HERE>
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_upload_workflow_operation_fields"
down_revision = "<PUT_CURRENT_HEAD_REVISION_HERE>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add only columns that do not already exist in your branch.
    # If prior control-plane simplification already added resource/progress/timestamps,
    # keep only stage/message from this migration.
    op.add_column("jobs", sa.Column("resource_type", sa.String(length=32), nullable=True))
    op.add_column("jobs", sa.Column("resource_id", sa.String(length=128), nullable=True))
    op.add_column("jobs", sa.Column("stage", sa.String(length=64), nullable=True))
    op.add_column("jobs", sa.Column("message", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("progress_current", sa.Integer(), nullable=True))
    op.add_column("jobs", sa.Column("progress_total", sa.Integer(), nullable=True))
    op.add_column("jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_jobs_resource", "jobs", ["resource_type", "resource_id"])
    op.create_index("ix_jobs_resource_status", "jobs", ["resource_type", "resource_id", "status"])

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

    op.execute("""
        UPDATE jobs
        SET stage = CASE
            WHEN status = 'queued' THEN 'queued'
            WHEN status = 'running' THEN 'indexing_lightrag'
            WHEN status = 'succeeded' THEN 'complete'
            WHEN status = 'failed' THEN 'failed'
            WHEN status = 'canceled' THEN 'failed'
            ELSE NULL
        END
        WHERE stage IS NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_jobs_resource_status", table_name="jobs")
    op.drop_index("ix_jobs_resource", table_name="jobs")
    op.drop_column("jobs", "finished_at")
    op.drop_column("jobs", "started_at")
    op.drop_column("jobs", "progress_total")
    op.drop_column("jobs", "progress_current")
    op.drop_column("jobs", "message")
    op.drop_column("jobs", "stage")
    op.drop_column("jobs", "resource_id")
    op.drop_column("jobs", "resource_type")
