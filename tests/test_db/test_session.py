"""Testes do módulo db.session."""

import pytest


def test_get_async_database_url_postgresql_replaced(monkeypatch):
    """_get_async_database_url troca postgresql:// por postgresql+asyncpg://."""
    from app.db import session

    class FakeSettings:
        DATABASE_URL = "postgresql://user:pass@host/db"

    monkeypatch.setattr("app.db.session.settings", FakeSettings)
    result = session._get_async_database_url()
    assert result == "postgresql+asyncpg://user:pass@host/db"


def test_get_async_database_url_psycopg2_replaced(monkeypatch):
    """_get_async_database_url troca postgresql+psycopg2 por postgresql+asyncpg."""
    from app.db import session

    class FakeSettings:
        DATABASE_URL = "postgresql+psycopg2://user:pass@host/db"

    monkeypatch.setattr("app.db.session.settings", FakeSettings)
    result = session._get_async_database_url()
    assert result == "postgresql+asyncpg://user:pass@host/db"


def test_get_async_database_url_other_returns_unchanged(monkeypatch):
    """_get_async_database_url retorna URL inalterada quando não é postgresql ou psycopg2."""
    from app.db import session

    class FakeSettings:
        DATABASE_URL = "sqlite+aiosqlite:///local.db"

    monkeypatch.setattr("app.db.session.settings", FakeSettings)
    result = session._get_async_database_url()
    assert result == "sqlite+aiosqlite:///local.db"
