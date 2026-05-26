"""add document domain column and lifecycle table

Revision ID: 0007_domain_lifecycle
Revises: 0006_operational_list_indexes
Create Date: 2026-05-26 13:45:00
"""

from collections.abc import Sequence
import json

from alembic import op
import sqlalchemy as sa

revision: str = "0007_domain_lifecycle"
down_revision: str | None = "0006_operational_list_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in set(sa.inspect(bind).get_table_names())


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    return any(index["name"] == index_name for index in sa.inspect(bind).get_indexes(table_name))


def _create_index_once(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _extract_domain_id(metadata: object) -> str | None:
    payload = metadata
    if isinstance(metadata, str):
        try:
            payload = json.loads(metadata)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    lightrag = payload.get("lightrag")
    if not isinstance(lightrag, dict):
        return None
    domain_id = lightrag.get("domain_id") or lightrag.get("domain")
    if domain_id is None:
        return None
    text = str(domain_id).strip()
    return text or None


def _backfill_document_domains() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, metadata FROM documents WHERE lightrag_domain_id IS NULL")).fetchall()
    for row in rows:
        domain_id = _extract_domain_id(row[1])
        if not domain_id:
            continue
        bind.execute(
            sa.text(
                "UPDATE documents SET lightrag_domain_id = :domain_id WHERE id = :document_id"
            ),
            {"domain_id": domain_id, "document_id": row[0]},
        )


def upgrade() -> None:
    if _table_exists("documents") and not _column_exists("documents", "lightrag_domain_id"):
        with op.batch_alter_table("documents") as batch_op:
            batch_op.add_column(sa.Column("lightrag_domain_id", sa.String(length=64), nullable=True))
        _create_index_once("ix_documents_lightrag_domain_id", "documents", ["lightrag_domain_id"])
        _backfill_document_domains()

    if not _table_exists("lightrag_domain_lifecycle"):
        op.create_table(
            "lightrag_domain_lifecycle",
            sa.Column("domain_id", sa.String(length=64), primary_key=True, nullable=False),
            sa.Column("state", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        _create_index_once("ix_lightrag_domain_lifecycle_state", "lightrag_domain_lifecycle", ["state"])
        _create_index_once(
            "ix_lightrag_domain_lifecycle_created_at", "lightrag_domain_lifecycle", ["created_at"]
        )


def downgrade() -> None:
    if _table_exists("lightrag_domain_lifecycle"):
        op.drop_index("ix_lightrag_domain_lifecycle_created_at", table_name="lightrag_domain_lifecycle")
        op.drop_index("ix_lightrag_domain_lifecycle_state", table_name="lightrag_domain_lifecycle")
        op.drop_table("lightrag_domain_lifecycle")

    if _table_exists("documents") and _column_exists("documents", "lightrag_domain_id"):
        if _index_exists("documents", "ix_documents_lightrag_domain_id"):
            op.drop_index("ix_documents_lightrag_domain_id", table_name="documents")
        with op.batch_alter_table("documents") as batch_op:
            batch_op.drop_column("lightrag_domain_id")
