# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI template with SQLModel (async SQLAlchemy), PostgreSQL, Redis, Celery task queue, and API documentation via Scalar. Uses `uv` for dependency management and Docker Compose for infrastructure.

**Tech Stack:**
- **FastAPI** 0.118+ - Modern, fast web framework
- **SQLModel** 0.0.22+ - SQL databases with Python type hints (SQLAlchemy + Pydantic)
- **Alembic** 1.14+ - Database migrations with async support
- **SQLAdmin** 0.20+ - Admin interface for database management
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
- `app/core/database.py` - Async engine, sync engine, session factory, init_db()
- `app/core/admin.py` - SQLAdmin configuration with auto-discovery
- `app/core/celery.py` - Celery app configuration
- `app/models/` - SQLModel table definitions (auto-imported by Alembic)
- `app/schemas/` - Pydantic request/response schemas
- `app/services/` - Business logic layer
- `app/tasks/` - Celery task definitions
- `app/admin/views.py` - Admin ModelView classes (auto-registered)

**Supporting directories:**
- `tests/` - Pytest suite with async support and fixtures
- `alembic/` - Database migrations with async support
- `docker/` - Docker configurations (Dockerfile.celery)
- `scripts/` - Utility scripts (export_openapi.py)

### Configuration System

**Settings** (`app/core/config.py`): Pydantic BaseSettings with required fields (no defaults for sensitive data). All settings load from `.env` file. Use `.env.example` as template.

**Dynamic properties** construct connection URLs from component variables:
- `DATABASE_URL` - Async PostgreSQL connection (asyncpg driver)
- `SYNC_DATABASE_URL` - Sync PostgreSQL connection (psycopg2 driver) for SQLAdmin
- `CELERY_BROKER_URL` - Redis broker for Celery (db 0)
- `CELERY_RESULT_BACKEND` - Redis result backend (db 1)
- `CELERY_TASKS_MODULE` - Computed from `CELERY_APP_NAME` (e.g., "app.tasks")

### Database Layer

**Engines**: Dual engine setup (`app/core/database.py`)
- `engine` (async) - For FastAPI endpoints via `create_async_engine()` with asyncpg driver
- `sync_engine` (sync) - For SQLAdmin interface via `create_engine()` with psycopg2 driver
- Both use `settings.DATABASE_ECHO` for SQL logging

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
- Broker: Redis db 0, Backend: Redis db 1
- Tasks auto-discovered from `app/tasks/` via glob pattern in `__init__.py`

**Task execution**:
- Trigger: `task_function.delay(*args)` returns AsyncResult with `.id`
- Status: `AsyncResult(task_id, app=celery_app)` → `.state`, `.result`, `.ready()`

**Docker services**:
- `celery-worker`: Worker process (background)
- `flower`: Monitoring UI at http://127.0.0.1:5555

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

### Admin Interface

**Access**: http://127.0.0.1:8000/admin

**Architecture** (`app/core/admin.py`):
- Auto-discovers all `ModelView` subclasses from `app/admin/views.py` using `inspect`
- No manual registration needed - just create view class in `app/admin/views.py`
- Uses `sync_engine` (psycopg2) for database operations

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

1. Create SQLModel class in `app/models/your_model.py` with `table=True` and explicit `__tablename__` - see `app/models/example.py` for pattern
2. Generate and apply migration: `make db-migrate message="add your_table"` then `make db-upgrade`

### Adding New API Endpoint

1. Create router in `app/api/your_endpoints.py` following `app/api/examples.py` pattern
2. Register in `app/api/router.py`: `api_router.include_router(your_endpoints.router, tags=["your_tag"])`
3. Use `get_session()` dependency for database access
4. Return SQLModel instances or Pydantic schemas

### Adding Celery Task

1. Define task function in `app/tasks/your_tasks.py` with `@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.task_name")` decorator - see `app/tasks/example_tasks.py`
2. Tasks auto-discovered via glob pattern in `app/tasks/__init__.py` - no manual import needed
3. Trigger in endpoint with `task_function.delay(*args)` or `task_function.apply_async()` for advanced options
4. Always use `@celery_app.task` (not `@shared_task`), tasks are synchronous, keep idempotent

### Adding Admin View

Create `ModelView` subclass in `app/admin/views.py` with `model=YourModel` parameter - auto-registered on startup.

### TypeScript Client Generation

Run `make client-generate` to export OpenAPI schema and generate TypeScript client in `./client/` with full type safety (*.ts). SQLModel classes become TypeScript types with full IDE autocomplete.

## Environment Configuration

Required variables in `.env` (see `.env.example` for complete list)
## Key Implementation Details

- **Package manager**: `uv` (not pip/poetry) - use `uv run` prefix for all Python commands
- **Database**: Dual engines - async (asyncpg) for API, sync (psycopg2) for admin
- **API responses**: Scalar docs preferred over default Swagger UI
- **Admin interface**: SQLAdmin at `/admin` with auto-discovery of ModelView classes
- **Environment**: Required `.env` file (no defaults for secrets/connection strings)
- **Docker networking**: Infrastructure services use service names as hostnames (e.g., `POSTGRES_HOST=postgres` in docker-compose, `localhost` for local dev)
- **Celery worker**: Runs in Docker container, requires infrastructure to be up for task execution
