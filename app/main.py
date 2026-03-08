from fastapi import FastAPI
import uvicorn

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


if __name__ == "__main__":
    import sys
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    # Sem reload ao rodar python app/main.py; para reload: uvicorn app.main:app --reload
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
