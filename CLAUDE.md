# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FastAPI template with SQLModel, Alembic, PostgreSQL, and Docker Compose for rapid development.

**Tech Stack:**
- **FastAPI** 0.118+ - Modern, fast web framework
- **SQLModel** 0.0.22+ - SQL databases with Python type hints (SQLAlchemy + Pydantic)
- **Alembic** 1.14+ - Database migrations with async support
- **PostgreSQL 17** (Alpine) - Primary database via Docker
- **Python** 3.10+ - Uses modern union syntax (`int | None`)
- **uv** - Fast Python package manager

## Quick Start

```bash
make setup                              # Create venv and install dependencies
cp .env.example .env                    # Configure environment
make infra-up                           # Start PostgreSQL
make db-migrate message="init"          # Generate initial migration
make db-upgrade                         # Apply migrations
make dev                                # Start server (http://127.0.0.1:8000)
```

**Common Commands:** (See `Makefile` or run `make help`)
- `make dev` - Start server with hot reload
- `make test` - Run all tests (specific: `uv run pytest tests/test_file.py::test_name`)
- `make lint` / `make format` - Code quality
- `make db-migrate message="desc"` → `make db-upgrade` - Database migrations
- `make client-generate` - Generate TypeScript client from OpenAPI schema
- `make infra-up` / `infra-down` / `infra-reset` - Infrastructure management

## Architecture

### Project Structure
```
app/
├── main.py           # FastAPI app with lifespan context manager, includes api_router with /api prefix
├── api/
│   ├── router.py     # Central API router aggregating all route modules
│   └── health.py     # Health check endpoint (/api/health)
├── core/
│   ├── config.py     # Settings using pydantic-settings (BaseSettings) from .env
│   └── database.py   # Async engine, session factory, get_session() dependency
├── models/           # SQLModel table definitions (auto-imported by Alembic)
│   └── example.py    # Example SQLModel
├── schemas/          # Pydantic request/response models
└── services/         # Business logic layer

scripts/              # Utility scripts
└── export_openapi.py # Exports OpenAPI schema for client generation

tests/                # Pytest suite with async support (asyncio_mode = "auto")
├── conftest.py       # Test fixtures: test_engine, db_session, client, sync_client
├── README.md         # Comprehensive testing guide
└── test_*.py         # Test files

alembic/              # Database migrations
├── versions/         # Migration files
└── env.py            # Alembic config with async SQLModel setup, auto-imports app/models/
```

### Key Design Decisions

- **API Routing**: All routes prefixed with `/api` (no versioning). Add endpoints in `app/api/` and include in `app/api/router.py`

- **Configuration**: `pydantic-settings` for environment-based config. Settings singleton in `app/core/config.py` loads from `.env`

- **Database**:
  - SQLModel ORM with async PostgreSQL (asyncpg driver)
  - Sessions via dependency injection: `get_session()` yields `AsyncSession`
  - Database URL auto-constructed: `postgresql+asyncpg://user:pass@host:port/db`
  - All operations are async - remember to `await`

- **Migrations**:
  - Alembic configured for async with auto-import of models from `app/models/`
  - `alembic/env.py` automatically discovers all `app/models/*.py` files
  - No manual imports needed in env.py

- **Testing**:
  - Test database: `{POSTGRES_DB}_test` (auto-created)
  - Transaction rollback for isolation (each test)
  - Fixtures in `conftest.py`: `db_session`, `client`, `sync_client`, `test_engine`
  - No `@pytest.mark.asyncio` needed (auto-detected)

### Adding New Endpoints

1. Create router in `app/api/users.py`:
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.core.database import get_session

   router = APIRouter()

   @router.get("/users")
   async def get_users(session: AsyncSession = Depends(get_session)):
       # Your logic here
       pass
   ```

2. Include in `app/api/router.py`:
   ```python
   from app.api import users
   api_router.include_router(users.router, tags=["users"])
   ```

### Working with Database

**Create a new model:**
1. Define in `app/models/user.py` (auto-imported by Alembic):
   ```python
   from sqlmodel import Field, SQLModel

   class User(SQLModel, table=True):
       __tablename__ = "users"
       id: int | None = Field(default=None, primary_key=True)
       email: str = Field(unique=True, index=True)
       name: str
   ```

2. Generate and apply migration:
   ```bash
   make db-migrate message="add users table"
   make db-upgrade
   ```

**Query in endpoints:**
```python
from sqlalchemy import select

@router.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user
```

## Testing

- **Run tests:** `make test` or `uv run pytest -v -s`
- **Test database:** PostgreSQL must be running (`make infra-up`)
- **Fixtures:** See `tests/conftest.py` for `db_session`, `client`, `sync_client`
- **Guide:** See `tests/README.md` for comprehensive examples and patterns

**Example test:**
```python
async def test_create_user(db_session: AsyncSession):
    user = User(email="test@example.com", name="Test")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id is not None
```

## TypeScript Client Generation

This project uses **@hey-api/openapi-ts** to generate type-safe TypeScript clients from the FastAPI OpenAPI schema.

**Generate client:**
```bash
make client-generate
```

This command:
1. Exports OpenAPI schema using `scripts/export_openapi.py`
2. Generates TypeScript client in `./client/` directory
3. Creates fully typed SDK with autocomplete for all endpoints

**Generated structure:**
```
client/
├── index.ts          # Main exports
├── sdk.gen.ts        # API functions (e.g., getExamplesApiExamplesGet)
├── types.gen.ts      # TypeScript types for all models
└── client.gen.ts     # HTTP client configuration
```

**Key features:**
- **SQLModel → TypeScript**: Database models automatically become TypeScript types
- **Type safety**: Full IDE autocomplete for requests, responses, and model fields
- **Path parameters**: Type-safe enforcement of required parameters
- **Nullability preserved**: `str | None` → `string | null`

**Example usage:**
```typescript
import { getExamplesApiExamplesGet, Example } from './client';

async function fetchExamples() {
  const response = await getExamplesApiExamplesGet({
    baseUrl: 'http://127.0.0.1:8000',
  });

  // TypeScript knows response.data is Array<Example>
  response.data?.forEach((example) => {
    console.log(example.name);  // Full autocomplete!
  });
}
```

**Workflow:**
1. Define SQLModel in `app/models/`
2. Create endpoint with `response_model=YourModel`
3. Include router in `app/api/router.py`
4. Run `make client-generate`
5. TypeScript client has full type safety for your model

**Important:**
- Re-run `make client-generate` after API changes
- `openapi.json` and `client/` are gitignored (regenerate as needed)

## Environment Configuration

Required variables in `.env` (see `.env.example`):
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

`DATABASE_URL` is auto-constructed from these components.

## Important Notes

- All database operations are async - always `await`
- Alembic auto-discovers models from `app/models/` - no manual imports needed
- Test database auto-created/dropped by fixtures with transaction rollback
- FastAPI lifespan context manager calls `init_db()` on startup
- API docs available at http://127.0.0.1:8000/docs
