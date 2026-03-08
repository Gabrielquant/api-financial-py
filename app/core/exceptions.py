"""Exceções customizadas da API."""


class AppException(Exception):
    """Exceção base da aplicação com status HTTP e mensagem."""

    def __init__(self, detail: str, status_code: int = 500) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class BadRequestError(AppException):
    """Validação de negócio ou requisição inválida (400)."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(detail=detail, status_code=400)


class UnauthorizedError(AppException):
    """Não autenticado ou credenciais inválidas (401)."""

    def __init__(self, detail: str = "Invalid credentials") -> None:
        super().__init__(detail=detail, status_code=401)


class ForbiddenError(AppException):
    """Sem permissão para o recurso (403)."""

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(detail=detail, status_code=403)


class NotFoundError(AppException):
    """Recurso não encontrado (404)."""

    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(detail=detail, status_code=404)


class ConflictError(AppException):
    """Conflito (ex.: email já cadastrado, ticker duplicado) (409)."""

    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(detail=detail, status_code=409)
