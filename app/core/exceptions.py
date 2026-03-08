"""Exceções customizadas da API."""


class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 500) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class BadRequestError(AppException):
    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(detail=detail, status_code=400)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Invalid credentials") -> None:
        super().__init__(detail=detail, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(detail=detail, status_code=403)


class NotFoundError(AppException):
    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(detail=detail, status_code=404)


class ConflictError(AppException):
    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(detail=detail, status_code=409)
