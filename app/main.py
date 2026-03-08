from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from app.api.routers import auth
from app.core.exceptions import AppException

app = FastAPI(
    title="Financial API",
    description="MVP de gestão financeira pessoal e acompanhamento de investimentos",
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "message": "Financial API"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(auth.router)


@app.exception_handler(AppException)
def app_exception_handler(_request, exc: AppException) -> JSONResponse:
    """Retorna respostas consistentes para exceções da aplicação."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    # Sem reload ao rodar python app/main.py; para reload: uvicorn app.main:app --reload
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
