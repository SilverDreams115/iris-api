"""add is_active to users"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ef6633ff199c"
down_revision: Union[str, None] = "83fad2748cb9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=True))

    op.execute(
        "UPDATE users SET is_active = TRUE WHERE is_active IS NULL"
    )

    op.alter_column("users", "is_active", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "is_active")
