"""Repositório de usuários."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User, UserRole


class UserRepository:
    """Acesso a dados de User."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        email: str,
        cognito_id: str,
        role: UserRole = UserRole.user,
    ) -> User:
        """Cria um usuário no banco."""
        user = User(
            email=email,
            cognito_id=cognito_id,
            role=role,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> User | None:
        """Busca usuário por id (UUID)."""
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Busca usuário por email."""
        return self._db.query(User).filter(User.email == email).first()

    def get_by_cognito_id(self, cognito_id: str) -> User | None:
        """Busca usuário por cognito_id (sub do Cognito)."""
        return self._db.query(User).filter(User.cognito_id == cognito_id).first()
