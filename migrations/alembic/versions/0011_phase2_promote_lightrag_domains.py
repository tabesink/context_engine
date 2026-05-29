"""promote lifecycle rows into first-class lightrag domains

Revision ID: 0011_phase2_lightrag_domains
Revises: 0010_phase1_operation_columns
Create Date: 2026-05-29 12:40:00
"""

from collections.abc import Sequence
import json

from alembic import op
import sqlalchemy as sa

revision: str = "0011_phase2_lightrag_domains"
down_revision: str | None = "0010_phase1_operation_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(sa.inspect(bind).get_table_names())


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _extract_display_name(metadata: object, fallback: str) -> str:
    payload = metadata
    if isinstance(metadata, str):
        try:
            payload = json.loads(metadata)
        except json.JSONDecodeError:
            return fallback
    if not isinstance(payload, dict):
        return fallback
    display_name = payload.get("display_name")
    if display_name is None:
        return fallback
    text = str(display_name).strip()
    return text or fallback


def _normalized_metadata(metadata: object) -> dict:
    payload = metadata
    if isinstance(metadata, str):
        try:
            payload = json.loads(metadata)
        except json.JSONDecodeError:
            return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _create_lightrag_domains_table() -> None:
    if _table_exists("lightrag_domains"):
        return
    op.create_table(
        "lightrag_domains",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("health_status", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def _backfill_from_lifecycle() -> None:
    if not _table_exists("lightrag_domain_lifecycle"):
        return
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT domain_id, state, error_message, metadata, created_at, updated_at
            FROM lightrag_domain_lifecycle
            """
        )
    ).fetchall()
    for domain_id, state, error_message, metadata, created_at, updated_at in rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO lightrag_domains (
                    id, display_name, state, health_status, error_message, metadata, created_at, updated_at
                ) VALUES (
                    :id, :display_name, :state, NULL, :error_message, :metadata, :created_at, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                    display_name = excluded.display_name,
                    state = excluded.state,
                    error_message = excluded.error_message,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at
                """
            ),
            {
                "id": domain_id,
                "display_name": _extract_display_name(metadata, str(domain_id)),
                "state": state or "active",
                "error_message": error_message,
                "metadata": json.dumps(_normalized_metadata(metadata)),
                "created_at": created_at,
                "updated_at": updated_at,
            },
        )


def upgrade() -> None:
    _create_lightrag_domains_table()
    if _column_exists("lightrag_domains", "health_status"):
        _backfill_from_lifecycle()


def downgrade() -> None:
    if _table_exists("lightrag_domains"):
        op.drop_table("lightrag_domains")
