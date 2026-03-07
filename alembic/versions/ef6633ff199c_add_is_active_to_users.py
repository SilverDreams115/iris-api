"""add is_active to users"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ef6633ff199c"
down_revision: str | None = "83fad2748cb9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=True))

    op.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL")

    op.alter_column("users", "is_active", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "is_active")
