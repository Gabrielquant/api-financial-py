"""Model Category."""

from app.db.base import Base


class Category(Base):
    """Categoria financeira (income/expense) por usuário."""

    __tablename__ = "categories"
