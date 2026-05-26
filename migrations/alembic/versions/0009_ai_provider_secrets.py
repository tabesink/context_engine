"""add encrypted ai provider secrets

Revision ID: 0009_ai_provider_secrets
Revises: 0008_ai_model_settings
Create Date: 2026-05-26 15:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0009_ai_provider_secrets"
down_revision: str | None = "0008_ai_model_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(sa.inspect(bind).get_table_names())


def upgrade() -> None:
    if not _table_exists("ai_provider_secrets"):
        op.create_table(
            "ai_provider_secrets",
            sa.Column("secret_name", sa.String(length=128), primary_key=True, nullable=False),
            sa.Column("encrypted_value", sa.Text(), nullable=False),
            sa.Column("updated_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )


def downgrade() -> None:
    if _table_exists("ai_provider_secrets"):
        op.drop_table("ai_provider_secrets")

