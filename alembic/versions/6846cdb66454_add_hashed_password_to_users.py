"""add hashed_password to users

Revision ID: 6846cdb66454
Revises: d060ca22e4fe
Create Date: 2026-03-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6846cdb66454"
down_revision: Union[str, None] = "d060ca22e4fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(), nullable=True))

    op.execute(
        "UPDATE users "
        "SET hashed_password = 'TEMP_PASSWORD_RESET_REQUIRED' "
        "WHERE hashed_password IS NULL"
    )

    op.alter_column("users", "hashed_password", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "hashed_password")
