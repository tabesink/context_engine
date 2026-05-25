"""baseline current context engine schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-20 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create core tables unless an existing create_all deployment already has them."""

    bind = op.get_bind()
    existing_tables = set(sa.inspect(bind).get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "documents" not in existing_tables:
        op.create_table(
            "documents",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("filename", sa.String(length=512), nullable=False),
            sa.Column("content_type", sa.String(length=255), nullable=False),
            sa.Column("storage_path", sa.String(length=1024), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("active_index_version", sa.Integer(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "jobs" not in existing_tables:
        op.create_table(
            "jobs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("kind", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "audit_logs" not in existing_tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("actor_id", sa.String(length=36), nullable=True),
            sa.Column("event", sa.String(length=128), nullable=False),
            sa.Column("target_id", sa.String(length=64), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "query_logs" not in existing_tables:
        op.create_table(
            "query_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("query", sa.Text(), nullable=False),
            sa.Column("mode", sa.String(length=32), nullable=False),
            sa.Column("latency_ms", sa.Integer(), nullable=False),
            sa.Column("evidence_count", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    """Baseline revision is intentionally irreversible."""
