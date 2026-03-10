"""Testes do serviço de dashboard."""

from app.services.dashboard_service import DashboardService


def test_dashboard_service_instantiation():
    """DashboardService pode ser instanciado."""
    svc = DashboardService()
    assert svc is not None
