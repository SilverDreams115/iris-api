"""add role to users"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "83fad2748cb9"
down_revision: Union[str, None] = "6846cdb66454"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(), nullable=True))

    op.execute(
        "UPDATE users SET role = 'user' WHERE role IS NULL"
    )

    op.alter_column("users", "role", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "role")
