"""Testes do repositório de ativos."""

from app.repositories.asset_repository import AssetRepository


def test_asset_repository_instantiation():
    """AssetRepository pode ser instanciado (cobre linhas 4-7)."""
    repo = AssetRepository()
    assert repo is not None
