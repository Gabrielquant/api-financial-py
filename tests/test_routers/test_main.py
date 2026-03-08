"""Testes das rotas raiz e health."""

import pytest
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
