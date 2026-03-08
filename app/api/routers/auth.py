"""Rotas de autenticação."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Registra novo usuário no Cognito. Confirme o email para poder fazer login."""
    return auth_service.register(
        email=body.email,
        password=body.password,
        db=db,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Autentica com email e senha no Cognito; retorna access e refresh token."""
    return auth_service.login(
        email=body.email,
        password=body.password,
        db=db,
    )
