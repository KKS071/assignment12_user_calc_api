# Assignment 12 — User & Calculation API

[![CI](https://github.com/KKS071/assignment12_user_calc_api/actions/workflows/ci.yml/badge.svg)](https://github.com/KKS071/assignment12_user_calc_api/actions)
[![Docker](https://img.shields.io/docker/v/kks59/601_module12?label=Docker%20Hub)](https://hub.docker.com/r/kks59/601_module12)

---

## Project Overview

This project is a production-ready REST API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. It demonstrates:

- **User registration & login** with JWT authentication (access + refresh tokens)
- **Calculation CRUD** (BREAD — Browse, Read, Edit, Add, Delete) for four arithmetic operations
- **Integration and unit tests** via `pytest` + `pytest-cov`
- **CI/CD pipeline** via GitHub Actions (test → vulnerability scan → Docker build & push)
- **Docker deployment** with Docker Compose (app + Postgres + pgAdmin)

**Repositories**

| Resource | URL |
|---|---|
| GitHub | https://github.com/KKS071/assignment12_user_calc_api |
| Docker Hub | https://hub.docker.com/r/kks59/601_module12 |

---

## Project Structure

```
.
├── app/
│   ├── main.py                 # FastAPI app, all routes
│   ├── database.py             # SQLAlchemy engine & session
│   ├── database_init.py        # create_all / drop_all helpers
│   ├── operations.py           # Pure arithmetic functions
│   ├── auth/
│   │   ├── dependencies.py     # get_current_user / get_current_active_user
│   │   ├── jwt.py              # Token creation, password hashing
│   │   └── redis.py            # Optional token blacklisting
│   ├── core/
│   │   └── config.py           # Pydantic settings
│   ├── models/
│   │   ├── user.py             # User SQLAlchemy model
│   │   └── calculation.py      # Calculation model (polymorphic)
│   └── schemas/
│       ├── base.py             # UserBase, PasswordMixin, UserCreate, UserLogin
│       ├── user.py             # Full user schemas with password validation
│       ├── calculation.py      # Calculation schemas
│       └── token.py            # Token schemas
├── tests/
│   ├── conftest.py             # Fixtures (DB, server, Faker)
│   ├── unit/
│   │   └── test_calculator.py  # Unit tests for operations.py
│   ├── integration/
│   │   ├── test_calculation.py
│   │   ├── test_calculation_schema.py
│   │   ├── test_database.py
│   │   ├── test_dependencies.py
│   │   ├── test_schema_base.py
│   │   ├── test_user.py
│   │   └── test_user_auth.py
│   └── e2e/
│       └── test_fastapi_calculator.py  # End-to-end tests vs live server
├── templates/
│   └── index.html              # Simple calculator UI
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Running Locally

### Prerequisites

- Python 3.10+
- PostgreSQL running locally (or use Docker Compose)

### 1 — Install dependencies

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Configure environment

Create a `.env` file (or export variables):

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
```

### 3 — Run the server

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000`.

### 4 — View interactive docs

| UI | URL |
|---|---|
| Swagger / OpenAPI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

### 5 — Run tests with coverage

```bash
# Unit + integration tests (fast, no live server)
pytest -m "not slow" --cov=app --cov-report=term-missing

# All tests including slow bulk tests
pytest --run-slow

# End-to-end tests (starts a live server automatically)
pytest tests/e2e/test_fastapi_calculator.py
```

---

## API Endpoints

### Auth

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login — returns JWT tokens |
| `POST` | `/auth/token` | OAuth2 form login (Swagger UI) |

### BREAD Calculations (requires `Authorization: Bearer <token>`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/calculations` | Create a calculation |
| `GET` | `/calculations` | List your calculations |
| `GET` | `/calculations/{id}` | Get a calculation by ID |
| `PUT` | `/calculations/{id}` | Update calculation inputs |
| `DELETE` | `/calculations/{id}` | Delete a calculation |

**Supported types:** `addition`, `subtraction`, `multiplication`, `division`

**Example request:**

```json
POST /calculations
{
  "type": "addition",
  "inputs": [10.5, 3, 2]
}
```

**Example response:**

```json
{
  "id": "...",
  "user_id": "...",
  "type": "addition",
  "inputs": [10.5, 3.0, 2.0],
  "result": 15.5,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Docker

### Build and run with Docker Compose

```bash
docker compose up --build
```

This starts:
- **web** — FastAPI on port 8000
- **db** — PostgreSQL 17 on port 5432
- **pgadmin** — pgAdmin 4 on port 5050 (`admin@example.com` / `admin`)

### Pull from Docker Hub

```bash
docker pull kks59/601_module12:latest
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET_KEY=... \
  kks59/601_module12:latest
```

---

## CI/CD Pipeline

The `.github/workflows/ci.yml` workflow runs on every push and pull request to `main`:

1. **Test job** — spins up a Postgres 17 service container, installs dependencies, and runs `pytest` with coverage.
2. **Docker job** (runs only on `main` after tests pass) — builds the Docker image and pushes it to Docker Hub using `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` repository secrets.

```
Push to main
    │
    ▼
┌──────────┐      pass      ┌────────────────────┐
│  pytest  │ ─────────────► │  docker build+push │
│  + cov   │                │  → Docker Hub      │
└──────────┘                └────────────────────┘
```

### Required GitHub Secrets

| Secret | Purpose |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

---
