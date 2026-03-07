"""add role to users"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "83fad2748cb9"
down_revision: str | None = "6846cdb66454"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(), nullable=True))

    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")

    op.alter_column("users", "role", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "role")
