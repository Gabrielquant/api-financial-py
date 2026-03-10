"""Testes dos schemas de dashboard."""

from app.schemas.dashboard import _Placeholder


def test_placeholder_model():
    """_Placeholder pode ser instanciado (schemas de dashboard)."""
    p = _Placeholder()
    assert p is not None
