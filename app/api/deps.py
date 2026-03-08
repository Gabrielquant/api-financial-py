"""Dependencies da API (sessão, usuário autenticado, etc.)."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db as _get_db


def get_db() -> Generator[Session, None, None]:
    """Fornece sessão do banco para a request."""
    yield from _get_db()
