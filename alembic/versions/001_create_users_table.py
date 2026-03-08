"""create users table

Revision ID: 001_users
Revises:
Create Date: 2025-03-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userrole_enum = postgresql.ENUM(
    "user", "admin", "auditor", name="userrole", create_type=False
)


def upgrade() -> None:
    # Cria o tipo enum só se não existir (evita erro em reexecução ou ambiente já parcialmente migrado)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                CREATE TYPE userrole AS ENUM ('user', 'admin', 'auditor');
            END IF;
        END
        $$;
    """)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("cognito_id", sa.String(255), nullable=False),
        sa.Column("role", userrole_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_cognito_id"), "users", ["cognito_id"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_cognito_id"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
