"""baseline current context engine schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-20 00:00:00
"""

from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Existing deployments already create these tables from SQLAlchemy metadata."""


def downgrade() -> None:
    """Baseline revision is intentionally irreversible."""
