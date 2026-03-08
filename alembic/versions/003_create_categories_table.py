"""create categories table

Revision ID: 003_categories
Revises: 002_remove_name
Create Date: 2025-03-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_categories"
down_revision: Union[str, None] = "002_remove_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'categorytype') THEN
                CREATE TYPE categorytype AS ENUM ('income', 'expense');
            END IF;
        END
        $$;
    """)
    categorytype_enum = postgresql.ENUM("income", "expense", name="categorytype", create_type=False)
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", categorytype_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_categories_user_id"), "categories", ["user_id"], unique=False)
    op.create_unique_constraint(
        "uq_categories_user_name_type",
        "categories",
        ["user_id", "name", "type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_categories_user_name_type", "categories", type_="unique")
    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.drop_table("categories")
    op.execute("DROP TYPE IF EXISTS categorytype")
