"""Model User."""

from app.db.base import Base


class User(Base):
    """Usuário autenticado (id, name, email, cognito_id, role, timestamps)."""

    __tablename__ = "users"
