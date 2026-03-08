# Financial API

MVP de gestão financeira pessoal e acompanhamento de investimentos em ações.

## Objetivo

API backend onde um usuário autenticado pode:

- Cadastrar-se e fazer login (Cognito/JWT)
- Cadastrar categorias financeiras
- Registrar receitas e despesas
- Consultar resumo financeiro mensal
- Cadastrar ativos (ações)
- Registrar compras de ações
- Consultar posição consolidada da carteira
- Consultar dashboard (receitas, despesas, saldo, total investido, patrimônio)

## Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic (migrations)
- Pydantic v2
- JWT via Cognito
- Pytest
- Docker / docker-compose
- Uvicorn

## Estrutura de pastas

```
app/
  main.py
  core/         # config, security, exceptions
  db/           # base, session
  models/       # user, category, transaction, asset, investment_transaction
  schemas/      # Pydantic (auth, user, category, transaction, asset, investment, portfolio, dashboard, common)
  repositories/ # acesso a dados
  services/     # lógica de negócio
  api/
    deps.py
    routers/    # auth, categories, transactions, assets, investments, portfolio, dashboard
tests/
alembic/
```

## Rodar localmente

1. Clone o repositório e entre na pasta do projeto.
2. Crie um ambiente virtual e ative:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Copie `.env.example` para `.env` e preencha com seus valores.
5. Suba o PostgreSQL (por exemplo via Docker) e configure `DATABASE_URL` no `.env`.
6. Rode as migrations:
   ```bash
   alembic upgrade head
   ```
7. Inicie a API:
   ```bash
   uvicorn app.main:app --reload
   ```
   A API estará em `http://localhost:8000`. Documentação em `/docs`.

## Rodar com Docker

```bash
cp .env.example .env
# Ajuste .env se necessário
docker compose up --build
```

App em `http://localhost:8000`, Postgres na porta 5432.

## Testes

```bash
pytest
```

## Próximos passos

- Implementar config (pydantic-settings), database session e models completos.
- Implementar autenticação (Cognito/JWT), services e repositories.
- Implementar rotas e registrar no `main.py`.
- Escrever testes e finalizar README com documentação dos endpoints.
