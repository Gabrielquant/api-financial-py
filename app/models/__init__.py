# Importar models para que Base.metadata os registre (Alembic).
from app.models.category import Category, CategoryType  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
