# Importar models para que Base.metadata os registre (Alembic).
from app.models.user import User, UserRole  # noqa: F401
