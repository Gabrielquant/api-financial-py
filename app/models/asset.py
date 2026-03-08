"""Model Asset."""

from app.db.base import Base


class Asset(Base):
    """Ativo de renda variável (ticker, name)."""

    __tablename__ = "assets"
