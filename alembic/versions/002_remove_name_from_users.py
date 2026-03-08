"""remove name from users

Revision ID: 002_remove_name
Revises: 001_users
Create Date: 2025-03-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_remove_name"
down_revision: Union[str, None] = "001_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "name")


def downgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(255), nullable=True))
