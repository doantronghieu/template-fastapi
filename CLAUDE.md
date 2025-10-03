# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI template with SQLModel (async SQLAlchemy), PostgreSQL, Redis, Celery task queue, and API documentation via Scalar. Uses `uv` for dependency management and Docker Compose for infrastructure.

**Tech Stack:**
- **FastAPI** 0.118+ - Modern, fast web framework
- **SQLModel** 0.0.22+ - SQL databases with Python type hints (SQLAlchemy + Pydantic)
- **Alembic** 1.14+ - Database migrations with async support
- **PostgreSQL 17** (Alpine) - Primary database via Docker
- **Redis 7** (Alpine) - Message broker for Celery
- **Celery** 5.5+ - Distributed task queue
- **Flower** 2.0+ - Celery monitoring UI
- **Python** 3.10+ - Uses modern union syntax (`int | None`)
- **uv** - Fast Python package manager

## Quick Start

```bash
# Initial setup (one-time)
make setup                                    # Create venv and install dependencies
cp .env.example .env                          # Configure environment variables
make infra-up                                 # Start PostgreSQL, Redis, Celery, Flower
make db-migrate message="init"                # Generate initial migration
make db-upgrade                               # Apply migrations

# Development workflow
make dev                                      # Start FastAPI server at http://127.0.0.1:8000
```

## Common Commands

### Development
- `make dev` - Start uvicorn with hot reload (http://127.0.0.1:8000)
- `make format` - Format code with ruff
- `make lint` - Run ruff linter with auto-fix
- `make test` - Run pytest suite

### Infrastructure (Docker Compose)
- `make infra-up` - Start PostgreSQL, Redis, Celery worker, Flower (http://127.0.0.1:5555)
- `make infra-down` - Stop all containers (preserves data in volumes)
- `make infra-reset` - Destroy volumes and recreate infrastructure with migrations
- `make infra-logs` - Follow logs from all services

### Database Migrations (Alembic)
- `make db-migrate message="description"` - Generate migration (auto-detects model changes)
- `make db-upgrade` - Apply pending migrations
- `make db-downgrade` - Rollback last migration
- Direct: `uv run alembic revision --autogenerate -m "message"` or `uv run alembic upgrade head`

### Testing
- `make test` - Run all tests
- `uv run pytest tests/test_file.py` - Run specific file
- `uv run pytest tests/test_file.py::test_name` - Run specific test
- `uv run pytest -v` - Verbose output
- `uv run pytest -s` - Show print statements
- `uv run pytest -m integration` - Run integration tests only
- Tests use `{POSTGRES_DB}_test` database with transaction rollback isolation

### Client Generation
- `make client-generate` - Generate TypeScript client from OpenAPI schema using Hey API

## Architecture

### Application Structure

**Core application files:**
- `app/main.py` - FastAPI app with lifespan context manager, Scalar docs at root
- `app/api/router.py` - Main API router aggregating all endpoint modules
- `app/api/health.py` - Health check endpoint
- `app/api/examples.py` - Example CRUD endpoints
- `app/api/tasks.py` - Celery task trigger and status endpoints
- `app/core/config.py` - Settings using Pydantic BaseSettings
- `app/core/database.py` - Async engine, session factory, init_db()
- `app/core/celery.py` - Celery app configuration
- `app/models/` - SQLModel table definitions (auto-imported by Alembic)
- `app/schemas/` - Pydantic request/response schemas
- `app/services/` - Business logic layer
- `app/tasks/` - Celery task definitions

**Supporting directories:**
- `tests/` - Pytest suite with async support and fixtures
- `alembic/` - Database migrations with async support
- `docker/` - Docker configurations (Dockerfile.celery)
- `scripts/` - Utility scripts (export_openapi.py)

### Configuration System

**Settings** (`app/core/config.py`): Pydantic BaseSettings with required fields (no defaults for sensitive data). All settings load from `.env` file. Use `.env.example` as template.

**Dynamic properties** construct connection URLs from component variables:
- `DATABASE_URL` - PostgreSQL connection string for SQLAlchemy
- `CELERY_BROKER_URL` - Redis broker for Celery (db 0)
- `CELERY_RESULT_BACKEND` - Redis result backend (db 1)
- `CELERY_TASKS_MODULE` - Computed from `CELERY_APP_NAME` (e.g., "app.tasks")

### Database Layer

**Engine**: Async SQLAlchemy via SQLModel (`app/core/database.py:10`)
- Created once at module import with `create_async_engine()`
- Uses `settings.DATABASE_URL` and `settings.DATABASE_ECHO`

**Sessions**: Async sessionmaker with `expire_on_commit=False` (`app/core/database.py:17`)
- Use `get_session()` dependency in endpoints for automatic session management
- Pattern: `async def endpoint(session: AsyncSession = Depends(get_session))`

**Models**: SQLModel tables in `app/models/` (`app/models/example.py`)
- Inherit from `SQLModel` with `table=True`
- Set `__tablename__` explicitly
- Use Field() for constraints (primary_key, index, max_length)

**Initialization**: `init_db()` creates all tables at startup via lifespan context manager (`app/main.py:12-18`)

### Alembic Migrations

**Auto-discovery**: Models auto-imported from `app/models/*.py` via glob pattern (`alembic/env.py:14-18`)
- Add new model file → migrations automatically detect it
- No need to manually import models in env.py

**Async support**: Uses `async_engine_from_config` and `run_sync()` (`alembic/env.py:74-86`)

**URL override**: `settings.DATABASE_URL` replaces alembic.ini URL at runtime (`alembic/env.py:25`)

### Celery Task Queue

**Configuration** (`app/core/celery.py`):
- Broker: Redis db 0
- Backend: Redis db 1
- Tasks auto-discovered from `app/tasks/` via `include=[settings.CELERY_TASKS_MODULE]`

**Task definition pattern** (`app/tasks/example_tasks.py`):
```python
@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.task_name")
def task_name(args) -> ReturnType:
    # Task logic
    return result
```

**Task execution** (`app/api/tasks.py`):
- Trigger: `task_function.delay(*args)` returns AsyncResult with `.id`
- Status check: `AsyncResult(task_id, app=celery_app)` → `.state`, `.result`, `.ready()`

**Docker services**:
- `celery-worker`: Runs worker with `uv run celery -A app.core.celery:celery_app worker`
- `flower`: Web UI for monitoring at http://127.0.0.1:5555

### API Layer

**Router aggregation** (`app/api/router.py`):
- Main `api_router` includes all endpoint routers
- Mounted at `/api` prefix in main.py
- Tags organize endpoints in API docs

**Endpoint pattern** (`app/api/examples.py`):
- Use `APIRouter()` at module level
- Depend on `get_session()` for database access
- Return SQLModel instances directly (auto-serialized)
- Use async/await with SQLAlchemy select()

**API Documentation**:
- Scalar UI at http://127.0.0.1:8000/scalar (default via root redirect)
- Interactive API reference with all endpoints, schemas, examples
- OpenAPI schema auto-generated from FastAPI

### Testing Infrastructure

**Configuration** (`pyproject.toml:29-34`):
- `asyncio_mode = "auto"` - No `@pytest.mark.asyncio` needed
- `testpaths = ["tests"]`
- Custom marker: `@pytest.mark.integration` for tests requiring Celery worker

**Test database** (`tests/conftest.py`):
- Name: `{POSTGRES_DB}_test` (e.g., `db_test`)
- Tables: Created once per session, dropped at end
- Isolation: Each test in transaction that rolls back

**Key fixtures** (all function-scoped except `test_engine`):
- `test_engine` (session) - Database engine
- `db_session` - Async session with transaction rollback
- `client` - Async HTTP client (httpx.AsyncClient) with DB override
- `sync_client` - Synchronous TestClient for non-async tests

See `tests/README.md` for detailed testing guide.

## Development Patterns

### Adding New Model

1. Create model in `app/models/your_model.py`:
   ```python
   from sqlmodel import Field, SQLModel

   class YourModel(SQLModel, table=True):
       __tablename__ = "your_table"
       id: int | None = Field(default=None, primary_key=True)
       name: str = Field(max_length=255)
   ```

2. Generate and apply migration:
   ```bash
   make db-migrate message="add your_table"
   make db-upgrade
   ```

### Adding New API Endpoint

1. Create router in `app/api/your_endpoints.py` following `app/api/examples.py` pattern
2. Register in `app/api/router.py`: `api_router.include_router(your_endpoints.router, tags=["your_tag"])`
3. Use `get_session()` dependency for database access
4. Return SQLModel instances or Pydantic schemas

### Adding Celery Task

1. Define task in `app/tasks/your_tasks.py`:
   ```python
   from app.core.celery import celery_app
   from app.core.config import settings

   @celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.your_task")
   def your_task(args) -> ReturnType:
       # Task logic here
       return result
   ```

2. Import in `app/tasks/__init__.py`:
   ```python
   from app.tasks.your_tasks import *  # noqa: F401, F403
   ```

3. Create endpoint to trigger task:
   ```python
   from app.tasks.your_tasks import your_task

   @router.post("/trigger")
   async def trigger_task():
       task = your_task.delay(*args)  # type: ignore[attr-defined]
       return {"task_id": task.id, "status": "queued"}
   ```

**Important notes:**
- Always use `@celery_app.task` (not `@shared_task`)
- Task names: `f"{settings.CELERY_TASKS_MODULE}.{function_name}"` pattern
- Tasks are synchronous (Celery handles concurrency)
- Use `task.delay()` for async execution or `task.apply_async()` for advanced options
- Keep tasks idempotent and handle failures gracefully

### TypeScript Client Generation

**Generate type-safe client:**
```bash
make client-generate
```

This exports OpenAPI schema and generates TypeScript client in `./client/` with full type safety.

**Generated structure:**
```
client/
├── index.ts          # Main exports
├── sdk.gen.ts        # API functions (e.g., getExamplesApiExamplesGet)
├── types.gen.ts      # TypeScript types for all models
└── client.gen.ts     # HTTP client configuration
```

**Usage example:**
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

**Key features:**
- SQLModel → TypeScript: Database models become TypeScript types
- Full IDE autocomplete for requests, responses, model fields
- Type-safe path parameters and nullability (`str | None` → `string | null`)

**Workflow:** Define SQLModel → Create endpoint → Include in router → Run `make client-generate` → Get typed client

## Environment Configuration

Required variables in `.env` (see `.env.example`):
```env
# PostgreSQL
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_database_name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery (optional, with defaults)
CELERY_APP_NAME=app
CELERY_TIMEZONE=UTC
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500
CELERY_RESULT_EXPIRES=3600
CELERY_TASK_ACKS_LATE=True
CELERY_WORKER_PREFETCH_MULTIPLIER=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# Flower
FLOWER_PORT=5555
```

**Auto-constructed URLs** (built from components above):
- `DATABASE_URL` - `postgresql+asyncpg://user:pass@host:port/db`
- `CELERY_BROKER_URL` - Redis db 0 (message broker)
- `CELERY_RESULT_BACKEND` - Redis db 1 (task results)
- `CELERY_TASKS_MODULE` - Derived from `CELERY_APP_NAME` (default: "app.tasks")

## Key Implementation Details

- **Package manager**: `uv` (not pip/poetry) - use `uv run` prefix for all Python commands
- **Database**: Async-only (asyncpg driver) - no sync engine available
- **API responses**: Scalar docs preferred over default Swagger UI
- **Environment**: Required `.env` file (no defaults for secrets/connection strings)
- **Docker networking**: Infrastructure services use service names as hostnames (e.g., `POSTGRES_HOST=postgres` in docker-compose, `localhost` for local dev)
- **Celery worker**: Runs in Docker container, requires infrastructure to be up for task execution
