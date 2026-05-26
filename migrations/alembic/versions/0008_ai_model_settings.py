"""add ai model profiles and defaults

Revision ID: 0008_ai_model_settings
Revises: 0007_domain_lifecycle
Create Date: 2026-05-26 15:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0008_ai_model_settings"
down_revision: str | None = "0007_domain_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(sa.inspect(bind).get_table_names())


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    return any(index["name"] == index_name for index in sa.inspect(bind).get_indexes(table_name))


def _create_index_once(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    if not _table_exists("ai_model_profiles"):
        op.create_table(
            "ai_model_profiles",
            sa.Column("id", sa.String(length=128), nullable=False, primary_key=True),
            sa.Column("kind", sa.String(length=32), nullable=False),
            sa.Column("provider", sa.String(length=32), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("model", sa.String(length=255), nullable=False),
            sa.Column("base_url", sa.String(length=1024), nullable=False),
            sa.Column("api_key_env_var", sa.String(length=128), nullable=True),
            sa.Column("binding", sa.String(length=64), nullable=False),
            sa.Column("dimensions", sa.Integer(), nullable=True),
            sa.Column("token_limit", sa.Integer(), nullable=True),
            sa.Column("send_dimensions", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("use_base64", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("extra", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        _create_index_once("ix_ai_model_profiles_kind", "ai_model_profiles", ["kind"])
        _create_index_once("ix_ai_model_profiles_provider", "ai_model_profiles", ["provider"])

    if not _table_exists("ai_model_settings"):
        op.create_table(
            "ai_model_settings",
            sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
            sa.Column(
                "default_llm_profile_id",
                sa.String(length=128),
                sa.ForeignKey("ai_model_profiles.id"),
                nullable=False,
            ),
            sa.Column(
                "default_embedding_profile_id",
                sa.String(length=128),
                sa.ForeignKey("ai_model_profiles.id"),
                nullable=False,
            ),
            sa.Column("updated_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )


def downgrade() -> None:
    if _table_exists("ai_model_settings"):
        op.drop_table("ai_model_settings")
    if _table_exists("ai_model_profiles"):
        if _index_exists("ai_model_profiles", "ix_ai_model_profiles_provider"):
            op.drop_index("ix_ai_model_profiles_provider", table_name="ai_model_profiles")
        if _index_exists("ai_model_profiles", "ix_ai_model_profiles_kind"):
            op.drop_index("ix_ai_model_profiles_kind", table_name="ai_model_profiles")
        op.drop_table("ai_model_profiles")

