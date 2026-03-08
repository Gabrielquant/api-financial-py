"""Rotas de transações."""

from fastapi import APIRouter

router = APIRouter(prefix="/transactions", tags=["transactions"])
