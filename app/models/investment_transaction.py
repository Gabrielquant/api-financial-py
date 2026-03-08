"""Model InvestmentTransaction."""

from app.db.base import Base


class InvestmentTransaction(Base):
    """Registro de compra de ação (user, asset, quantity, price, fees, date)."""

    __tablename__ = "investment_transactions"
