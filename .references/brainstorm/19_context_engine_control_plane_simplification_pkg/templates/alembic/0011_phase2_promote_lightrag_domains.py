"""phase2 promote LightRAG domains to first-class rows

Revision ID: 0011_phase2_promote_lightrag_domains
Revises: 0010_phase1_add_operation_columns
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_phase2_promote_lightrag_domains"
down_revision = "0010_phase1_add_operation_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Conservative path: preserve existing lifecycle data by renaming the table.
    # If the table has already been renamed in your branch, replace this with guards or manual migration.
    op.rename_table("lightrag_domain_lifecycle", "lightrag_domains")
    op.alter_column("lightrag_domains", "domain_id", new_column_name="id", existing_type=sa.String(length=64))

    op.add_column("lightrag_domains", sa.Column("display_name", sa.String(length=255), nullable=True))
    op.add_column("lightrag_domains", sa.Column("health_status", sa.String(length=32), nullable=True))
    op.add_column("lightrag_domains", sa.Column("base_url", sa.String(length=1024), nullable=True))
    op.add_column("lightrag_domains", sa.Column("container_name", sa.String(length=255), nullable=True))
    op.add_column("lightrag_domains", sa.Column("host_port", sa.Integer(), nullable=True))
    op.add_column("lightrag_domains", sa.Column("embedding_profile_id", sa.String(length=128), nullable=True))
    op.add_column("lightrag_domains", sa.Column("created_by_user_id", sa.String(length=36), nullable=True))

    op.create_index("ix_lightrag_domains_state", "lightrag_domains", ["state"])
    op.create_index("ix_lightrag_domains_health_status", "lightrag_domains", ["health_status"])

    op.create_foreign_key(
        "fk_lightrag_domains_embedding_profile_id_ai_model_profiles",
        "lightrag_domains",
        "ai_model_profiles",
        ["embedding_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_lightrag_domains_created_by_user_id_users",
        "lightrag_domains",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Safe display name backfill. Keep DB-specific JSON extraction out of the template.
    # Coding agent may replace with PostgreSQL JSONB extraction if desired.
    op.execute("""
        UPDATE lightrag_domains
        SET display_name = id
        WHERE display_name IS NULL
    """)

    # Do NOT add documents.lightrag_domain_id FK in the same migration until data audit passes.
    # See 04_database_migration_strategy.md for the audit query.


def downgrade() -> None:
    op.drop_constraint("fk_lightrag_domains_created_by_user_id_users", "lightrag_domains", type_="foreignkey")
    op.drop_constraint("fk_lightrag_domains_embedding_profile_id_ai_model_profiles", "lightrag_domains", type_="foreignkey")
    op.drop_index("ix_lightrag_domains_health_status", table_name="lightrag_domains")
    op.drop_index("ix_lightrag_domains_state", table_name="lightrag_domains")

    op.drop_column("lightrag_domains", "created_by_user_id")
    op.drop_column("lightrag_domains", "embedding_profile_id")
    op.drop_column("lightrag_domains", "host_port")
    op.drop_column("lightrag_domains", "container_name")
    op.drop_column("lightrag_domains", "base_url")
    op.drop_column("lightrag_domains", "health_status")
    op.drop_column("lightrag_domains", "display_name")

    op.alter_column("lightrag_domains", "id", new_column_name="domain_id", existing_type=sa.String(length=64))
    op.rename_table("lightrag_domains", "lightrag_domain_lifecycle")
