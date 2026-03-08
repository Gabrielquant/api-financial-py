"""create transactions table

Revision ID: 004_transactions
Revises: 003_categories
Create Date: 2025-03-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_transactions"
down_revision: Union[str, None] = "003_categories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    categorytype_enum = postgresql.ENUM(
        "income", "expense", name="categorytype", create_type=False
    )
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("type", categorytype_enum, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_category_id"),
        "transactions",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_transaction_date"),
        "transactions",
        ["transaction_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_type"), "transactions", ["type"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_type"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_transaction_date"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")
