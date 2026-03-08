"""Model Transaction."""

from app.db.base import Base


class Transaction(Base):
    """Lançamento financeiro (receita/despesa)."""

    __tablename__ = "transactions"
