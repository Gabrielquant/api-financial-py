# Financial API — Apresentação do Projeto

API REST para **gestão financeira pessoal**: usuários autenticados podem cadastrar categorias, registrar receitas e despesas e consultar resumo mensal. O documento abaixo explica, ponto a ponto, como o projeto funciona.

---

## 1. Visão geral

- **O que é:** Backend em Python (FastAPI) que expõe endpoints de autenticação, categorias e transações.
- **Autenticação:** AWS Cognito (registro, login, refresh de token). As rotas protegidas validam o JWT no header `Authorization`.
- **Banco de dados:** PostgreSQL com acesso assíncrono (SQLAlchemy 2.0 + asyncpg). Migrações com Alembic.
- **Fluxo de uma requisição:**  
  `Cliente HTTP` → **Router** (FastAPI) → **Service** (regras de negócio) → **Repository** (acesso ao banco) → **Model** (tabela).

Cada camada tem uma responsabilidade clara; isso facilita testes e manutenção.

---

## 2. Estrutura de pastas

```
app/
  main.py              # Ponto de entrada: cria o app FastAPI, registra rotas e tratador de exceções
  core/                 # Configuração, segurança e exceções globais
    config.py           # Variáveis de ambiente (pydantic-settings)
    security.py         # JWT/Cognito: extração do token, validação, secret_hash
    exceptions.py       # AppException e subclasses (BadRequest, Unauthorized, NotFound, etc.)
  db/
    base.py             # Base declarativa do SQLAlchemy (todos os models herdam daqui)
    session.py          # Engine assíncrona, AsyncSessionLocal, get_db() para injeção
  models/               # Entidades do banco (SQLAlchemy ORM)
    user.py             # User (id, email, cognito_id, role, timestamps)
    category.py         # Category (user_id, name, type: income|expense)
    transaction.py      # Transaction (user_id, category_id, amount, type, description, transaction_date)
  schemas/              # Contratos de entrada/saída (Pydantic)
    auth.py             # RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, CognitoTokenPayload
    user.py             # UserResponse
    category.py         # CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse
    transaction.py      # TransactionCreate, TransactionUpdate, TransactionResponse, MonthlySummaryResponse
  repositories/         # Acesso a dados: apenas operações de banco
    user_repository.py
    category_repository.py
    transaction_repository.py
  services/             # Lógica de negócio e orquestração
    auth_service.py     # register, login, refresh (Cognito + criação/sync de User)
    category_service.py # create, list_by_user, get_by_id, delete, update
    transaction_service.py # create, list_by_user, get_monthly_summary, update
  api/
    deps.py             # get_db, get_current_user (dependências FastAPI)
    routers/
      auth.py           # POST /auth/register, /auth/login, /auth/refresh, GET /auth/me
      categories.py     # POST/GET/DELETE/PATCH /categories
      transactions.py   # POST/GET/PATCH /transactions, GET /transactions/monthly-summary
tests/                  # Testes (conftest, test_routers, test_services)
alembic/                # Migrações do banco (versions/, env.py)
```

---

## 3. Como cada parte funciona

### 3.1 `app/main.py`

- Cria a instância do **FastAPI** (título, descrição, versão).
- Define rotas raiz: `GET /` e `GET /health`.
- **Inclui os routers:** `auth`, `categories`, `transactions` (cada um com seu prefixo e tag).
- Registra um **exception handler** para `AppException`: qualquer `raise` de `BadRequestError`, `UnauthorizedError`, `NotFoundError`, etc. é convertido em resposta JSON com `detail` e `status_code` corretos.
- Pode ser rodado com `uvicorn app.main:app`.

Ou seja: o `main.py` é só a montagem do app e o tratamento global de erros; a lógica fica nos routers, services e repositories.

---

### 3.2 Configuração (`app/core/config.py`)

- Usa **pydantic-settings**: lê variáveis de ambiente (e arquivo `.env`).
- Define valores padrão para: `DATABASE_URL`, `COGNITO_*`, `AWS_*`, `SECRET_KEY`, `DEBUG`.
- Quem precisa de config importa `settings` daqui (por exemplo `app.db.session` e `app.core.security`).

---

### 3.3 Banco de dados (`app/db/`)

- **base.py:** Define a classe `Base` (DeclarativeBase do SQLAlchemy). Todos os models (`User`, `Category`, `Transaction`) herdam de `Base` e declaram colunas e relacionamentos.
- **session.py:**
  - Converte `DATABASE_URL` para o driver assíncrono (`postgresql+asyncpg://...`).
  - Cria o **engine** e o **AsyncSessionLocal**.
  - **get_db()** é um generator que abre uma sessão, entrega ao endpoint e fecha ao final. Usado com `Depends(get_db)` no FastAPI.

Toda rota que precisa de banco recebe `db: AsyncSession = Depends(get_db)` e repassa para services/repositories.

---

### 3.4 Models (`app/models/`)

- **User:** id (UUID), email, cognito_id (vínculo com Cognito), role (enum), created_at, updated_at, deleted_at. Relacionamentos: `categories`, `transactions`.
- **Category:** id, user_id (FK → users), name, type (income | expense). Constraint único: (user_id, name, type). Relacionamentos: `user`, `transactions`.
- **Transaction:** id, user_id, category_id, amount (Numeric), type (income|expense), description, transaction_date, created_at. Relacionamentos: `user`, `category`.

Os models são a “cara” das tabelas no código; não contêm regras de negócio pesadas, só estrutura e relacionamentos.

---

### 3.5 Schemas (`app/schemas/`)

- **Objetivo:** Definir o formato dos dados que **entram** (body/query) e **saem** (response) da API.
- **auth:** `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `TokenResponse`, `CognitoTokenPayload` (payload do JWT após validação).
- **user:** `UserResponse` (usado em `/auth/me`).
- **category:** `CategoryCreate`, `CategoryUpdate`, `CategoryResponse`, `CategoryListResponse`.
- **transaction:** `TransactionCreate`, `TransactionUpdate`, `TransactionResponse`, `TransactionListResponse`, `MonthlySummaryResponse`.

Validações (ex.: email, tamanho de senha, `amount > 0`) ficam nos schemas Pydantic; erros de validação são tratados automaticamente pelo FastAPI.

---

### 3.6 Segurança e dependências (`app/core/security.py` e `app/api/deps.py`)

- **security.py:**
  - `cognito_secret_hash`: usado nas chamadas ao Cognito (sign up, initiate_auth, refresh).
  - `get_token_from_authorization_header`: lê o Bearer token do header; levanta `UnauthorizedError` se faltar ou for inválido.
  - `decode_and_validate_cognito_token`: busca as chaves JWKS do Cognito, decodifica o JWT, valida assinatura e expiração e retorna um `CognitoTokenPayload` (sub, email, etc.).

- **deps.py:**
  - **get_db:** já explicado (sessão assíncrona).
  - **get_current_user:** usa `get_token_from_authorization_header` e `decode_and_validate_cognito_token`, depois busca o usuário no banco por `cognito_id` (UserRepository). Se não achar, levanta `UnauthorizedError`. Rotas protegidas declaram `current_user: User = Depends(get_current_user)`.

Assim, qualquer rota que use `get_current_user` exige um JWT válido do Cognito e tem o `User` carregado.

---

### 3.7 Exceções (`app/core/exceptions.py`)

- **AppException:** base com `detail` e `status_code`.
- Subclasses: `BadRequestError` (400), `UnauthorizedError` (401), `ForbiddenError` (403), `NotFoundError` (404), `ConflictError` (409).

Services e deps fazem `raise UnauthorizedError("...")`, `raise NotFoundError("...")`, etc. O handler em `main.py` transforma isso em `JSONResponse` com o status e o `detail`, mantendo a API consistente.

---

### 3.8 Repositories (`app/repositories/`)

- **Papel:** Única camada que executa SQL/ORM. Métodos como `create`, `get_by_id`, `get_by_email`, `list_by_user_id`, `update`, `delete`, `list_by_filters`, `get_monthly_totals`.
- Recebem `AsyncSession` no construtor (ou por parâmetro) e usam `self._db` para `add`, `commit`, `refresh`, `execute(select(...))`, etc.
- **Não** aplicam regras de negócio (ex.: “usuário pode editar só a própria categoria”); isso fica nos services.

---

### 3.9 Services (`app/services/`)

- **auth_service:**  
  - **register:** gera secret_hash, chama Cognito sign_up, confirma e verifica email, depois cria ou ignora usuário no banco (UserRepository). Trata exceções do Cognito (ex.: email já existe → `ConflictError`).  
  - **login:** confere se o email existe no banco, chama Cognito initiate_auth com USER_PASSWORD_AUTH, devolve `TokenResponse`.  
  - **refresh:** valida usuário por email, chama Cognito REFRESH_TOKEN_AUTH, devolve novos tokens.

- **category_service:**  
  - create: normaliza nome, verifica duplicata (user + name + type), chama repository.  
  - list_by_user, get_by_id, delete, update: checam sempre se o recurso existe e se pertence ao `user_id` (404 ou 403 quando aplicável).

- **transaction_service:**  
  - create: valida que a categoria existe, pertence ao usuário e que o tipo da transação bate com o da categoria; depois cria via repository.  
  - list_by_user: delega ao repository com filtros (mês, ano, tipo, category_id).  
  - get_monthly_summary: usa repository para somar receitas e despesas do mês/ano e calcula balance e saving_rate.  
  - update: valida transação e categoria (existência e dono) e tipo antes de atualizar.

Ou seja: **toda regra de negócio e validação que depende de mais de um model ou de chamada externa (Cognito) está nos services.**

---

### 3.10 Routers (`app/api/routers/`)

- **auth:**  
  - POST `/auth/register` → body RegisterRequest → auth_service.register.  
  - POST `/auth/login` → LoginRequest → auth_service.login → TokenResponse.  
  - POST `/auth/refresh` → RefreshRequest → auth_service.refresh → TokenResponse.  
  - GET `/auth/me` → depende de `get_current_user` → retorna UserResponse.

- **categories:**  
  - POST `/categories` → CategoryCreate + get_current_user + get_db → CategoryService(db).create → CategoryResponse.  
  - GET `/categories` → list_by_user → CategoryListResponse.  
  - DELETE `/categories/{id}` → verifica dono e deleta.  
  - PATCH `/categories/{id}` → CategoryUpdate → update → CategoryResponse.

- **transactions:**  
  - POST `/transactions` → TransactionCreate + current_user + db → TransactionService(db).create.  
  - GET `/transactions` → query params opcionais (month, year, type, category_id) → list_by_user → TransactionListResponse.  
  - GET `/transactions/monthly-summary` → month, year obrigatórios → get_monthly_summary → MonthlySummaryResponse.  
  - PATCH `/transactions/{id}` → TransactionUpdate → update → TransactionResponse.

Os routers são finos: recebem o request, extraem body/params, chamam o service (passando user_id e db) e convertem o retorno em schema de resposta.

---

### 3.11 Migrações (Alembic)

- **alembic/env.py** carrega `.env`, lê `DATABASE_URL` e usa os **models** (via `Base.metadata`) como alvo das migrações.
- As versões em `alembic/versions/` criam/alteram tabelas (users, categories, transactions, etc.).  
Comando típico: `alembic upgrade head` para aplicar todas; `alembic revision --autogenerate` para gerar nova migração a partir dos models.

---

## 4. Stack e ferramentas

- **Python 3.12+**
- **FastAPI** (API e injeção de dependências)
- **SQLAlchemy 2.0** (ORM assíncrono)
- **PostgreSQL** (driver asyncpg)
- **Pydantic v2** (schemas e config)
- **Alembic** (migrações)
- **AWS Cognito** (autenticação; JWT validado via JWKS)
- **Uvicorn** (servidor ASGI)
- **pytest** (testes)
- **Ruff** (lint e formatação; config no `pyproject.toml`)

---

## 5. Como rodar o projeto

1. **Ambiente**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   ```
2. **Dependências** (o projeto usa `pyproject.toml`)
   ```bash
   pip install -e .
   # ou, se tiver uv: uv sync
   ```
3. **Variáveis de ambiente**  
   Crie um `.env` na raiz (ou use um `.env.example` como base) com pelo menos:
   - `DATABASE_URL` (ex.: `postgresql://user:password@localhost:5432/financial_db`)
   - `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET` (e opcionalmente `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` se não usar credenciais padrão do ambiente).
4. **Banco**  
   Subir PostgreSQL (local ou Docker) e criar o banco referenciado em `DATABASE_URL`.
5. **Migrações**
   ```bash
   alembic upgrade head
   ```
6. **API**
   ```bash
   uvicorn app.main:app --reload
   ```
   - API: `http://localhost:8000`  
   - Documentação interativa: `http://localhost:8000/docs`

---

## 6. Testes

- **conftest.py** provavelmente define fixtures (client, db, usuário de teste, etc.).
- **test_routers/** e **test_services/** testam endpoints e lógica de negócio.

Comando:

```bash
pytest
```

---

## 7. Resumo do fluxo (exemplo: criar transação)

1. Cliente envia `POST /transactions` com body (category_id, amount, type, description, transaction_date) e header `Authorization: Bearer <access_token>`.
2. **Router** recebe o request; FastAPI valida o body com `TransactionCreate` e injeta `db` e `current_user` (deps).
3. **get_current_user** extrai o token, valida com Cognito JWKS e busca o User no banco; retorna o User.
4. **TransactionService(db).create(user_id, body)** valida categoria (existência, dono, tipo), depois **TransactionRepository(db).create(...)** persiste a transação.
5. **Router** converte o model em `TransactionResponse` e devolve 201.

Esse padrão (Router → Service → Repository → Model) se repete em categorias e auth (com auth_service falando com Cognito e UserRepository). O README acima cobre cada um desses pontos para você conseguir navegar e entender o projeto como uma apresentação completa.
