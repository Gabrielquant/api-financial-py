def test_get_async_database_url_postgresql_replaced(monkeypatch):
    from app.db import session

    class FakeSettings:
        DATABASE_URL = "postgresql://user:pass@host/db"

    monkeypatch.setattr("app.db.session.settings", FakeSettings)
    result = session._get_async_database_url()
    assert result == "postgresql+asyncpg://user:pass@host/db"


def test_get_async_database_url_psycopg2_replaced(monkeypatch):
    from app.db import session

    class FakeSettings:
        DATABASE_URL = "postgresql+psycopg2://user:pass@host/db"

    monkeypatch.setattr("app.db.session.settings", FakeSettings)
    result = session._get_async_database_url()
    assert result == "postgresql+asyncpg://user:pass@host/db"


def test_get_async_database_url_other_returns_unchanged(monkeypatch):
    from app.db import session

    class FakeSettings:
        DATABASE_URL = "sqlite+aiosqlite:///local.db"

    monkeypatch.setattr("app.db.session.settings", FakeSettings)
    result = session._get_async_database_url()
    assert result == "sqlite+aiosqlite:///local.db"
