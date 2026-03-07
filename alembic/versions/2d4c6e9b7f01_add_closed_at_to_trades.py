"""add closed at to trades

Revision ID: 2d4c6e9b7f01
Revises: 21f850c64110
Create Date: 2026-03-06 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2d4c6e9b7f01"
down_revision: str | None = "21f850c64110"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("trades", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("trades", "closed_at")
