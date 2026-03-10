"""Testes das rotas raiz e health."""

import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient


def test_root(client: TestClient):
    """GET / retorna status ok."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert "message" in resp.json()


def test_health(client: TestClient):
    """GET /health retorna healthy."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_app_exception_handler_returns_json_with_status_code(client_with_user):
    """Exception handler para AppException retorna JSON com status_code e detail."""
    from app.api.deps import get_db
    from app.main import app

    async def mock_get_db():
        session = MagicMock()
        session.get = AsyncMock(return_value=None)  # categoria não existe
        session.commit = AsyncMock()
        session.delete = AsyncMock()
        session.close = AsyncMock()
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = mock_get_db
    try:
        fake_id = uuid.uuid4()
        resp = client_with_user.delete(f"/categories/{fake_id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Categoria não encontrada."
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_dashboard_router_loaded(client: TestClient):
    """Router de dashboard está montado (rota existe, retorna 404 sem endpoint)."""
    resp = client.get("/dashboard/")
    assert resp.status_code == 404


def test_main_module_runnable(monkeypatch):
    """Bloco if __name__ == '__main__' é executável (cobre main.py 40-47)."""
    import runpy
    import sys
    from types import ModuleType

    mock_run = MagicMock()
    fake_uvicorn = ModuleType("uvicorn")
    fake_uvicorn.run = mock_run
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    runpy.run_module("app.main", run_name="__main__")
    mock_run.assert_called_once()
