"""Segurança: secret hash Cognito, validação JWT (futuro)."""

import base64
import hmac
import hashlib


def cognito_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calcula o SECRET_HASH para Cognito (app client com secret).

    Obrigatório em SignUp e InitiateAuth quando o app client tem client secret.
    """
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode("utf-8")
