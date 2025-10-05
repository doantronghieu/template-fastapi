# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI template with SQLModel (async SQLAlchemy), PostgreSQL, Redis, Celery task queue, and API documentation via Scalar. Uses `uv` for dependency management and Docker Compose for infrastructure.

**Tech Stack:**
- **FastAPI** 0.118+ - Modern, fast web framework
- **SQLModel** 0.0.22+ - SQL databases with Python type hints (SQLAlchemy + Pydantic)
- **Alembic** 1.14+ - Database migrations with async support
- **SQLAdmin** 0.20+ - Admin interface for database management
- **Jinja2** 3.1+ - Server-side templating engine
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
- `app/main.py` - FastAPI app with lifespan context manager, static files, page routes, API routes
- `app/api/router.py` - Main API router aggregating all endpoint modules
- `app/api/pages.py` - Page routes returning Jinja2 templates
- `app/api/health.py` - Health check endpoint
- `app/api/examples.py` - Example CRUD endpoints
- `app/api/tasks.py` - Celery task trigger and status endpoints
- `app/core/config.py` - Settings using Pydantic BaseSettings
- `app/core/database.py` - Async engine, sync engine, session factory, init_db()
- `app/core/dependencies.py` - Centralized DI providers with type aliases
- `app/core/templates.py` - Jinja2Templates instance with directory configuration
- `app/core/admin.py` - SQLAdmin configuration with auto-discovery
- `app/core/celery.py` - Celery app configuration
- `app/models/` - SQLModel table definitions (auto-imported by Alembic)
- `app/schemas/` - Pydantic request/response schemas
- `app/services/` - Business logic layer with auto-discovery
- `app/tasks/` - Celery task definitions
- `app/admin/views.py` - Admin ModelView classes (auto-registered)

**Supporting directories:**
- `templates/` - Jinja2 templates (base.html, pages, partials)
- `static/` - CSS, JavaScript, images
- `tests/` - Pytest suite with async support and fixtures
- `alembic/` - Database migrations with async support
- `docker/` - Docker configurations (Dockerfile.celery)
- `scripts/` - Utility scripts (export_openapi.py)

### Configuration System

Pydantic BaseSettings with required fields (no defaults for sensitive data). All settings load from `.env` file via `python-dotenv` in `app/main.py`. Use `.env.example` as template.

**Environment Loading**: `.env` file loaded into `os.environ` via `load_dotenv()` at app startup - required for third-party libraries (LangChain, etc.) that read from environment variables.

**Dynamic properties:**
- `DATABASE_URL` - Async PostgreSQL connection (asyncpg driver)
- `SYNC_DATABASE_URL` - Sync PostgreSQL connection (psycopg2 driver) for SQLAdmin
- `CELERY_BROKER_URL` - Redis broker for Celery (db 0)
- `CELERY_RESULT_BACKEND` - Redis result backend (db 1)
- `CELERY_TASKS_MODULE` - Computed from `CELERY_APP_NAME` (e.g., "app.tasks")

### Database Layer

**Engines**: Dual engine setup
- `engine` (async) - For FastAPI endpoints via `create_async_engine()` with asyncpg driver
- `sync_engine` (sync) - For SQLAdmin interface via `create_engine()` with psycopg2 driver
- Both use `settings.DATABASE_ECHO` for SQL logging

**Sessions**: Async sessionmaker with `expire_on_commit=False`
- Inject via `SessionDep` type alias from `app.core.dependencies`
- Pattern: `async def endpoint(session: SessionDep)` for clean signatures

**Models**: SQLModel tables in `app/models/`
- Inherit from `SQLModel` with `table=True` and explicit `__tablename__`
- Use `Field()` for constraints (primary_key, index, max_length)

**Initialization**: `init_db()` creates all tables at startup via lifespan context manager

### Dependency Injection

**Centralized providers** in `app/core/dependencies.py`

**Service layer pattern** in `app/services/`:
- Service classes encapsulate business logic (e.g., `ExampleService`)
- Provider functions return service instances (e.g., `get_example_service(session: SessionDep)`)
- Type aliases for injection (e.g., `ExampleServiceDep = Annotated[ExampleService, Depends(get_example_service)]`)
- Auto-discovery: All services automatically imported via `app/services/__init__.py`

**Endpoint pattern**: Inject services via type aliases - `async def endpoint(service: ExampleServiceDep)`

### Alembic Migrations

**Auto-discovery**: Models auto-imported from `app/models/*.py` via glob pattern
- Add new model file → migrations automatically detect it
- No manual import needed in env.py

**Async support**: Uses `async_engine_from_config` and `run_sync()`

**URL override**: `settings.DATABASE_URL` replaces alembic.ini URL at runtime

### Celery Task Queue

**Configuration**: Broker (Redis db 0), Backend (Redis db 1)
- Tasks auto-discovered from `app/tasks/` via glob pattern in `__init__.py`

**Task execution**:
- Trigger: Call `task_function.delay(*args)` to get AsyncResult with `.id`
- Status: Use `AsyncResult(task_id, app=celery_app)` to access `.state`, `.result`, `.ready()`

**Docker services**:
- `celery-worker`: Worker process (background)
- `flower`: Monitoring UI at http://127.0.0.1:5555

### API Layer

**Router aggregation**: Main `api_router` includes all endpoint routers
- Mounted at `/api` prefix in main.py
- Tags organize endpoints in API docs

**Endpoint pattern**: Create `APIRouter()` at module level
- Inject services via type aliases (e.g., `service: ExampleServiceDep`)
- Return SQLModel instances directly (auto-serialized)
- Business logic in service layer, endpoints handle HTTP concerns only

**API Documentation**:
- Scalar UI at http://127.0.0.1:8000/scalar
- Interactive API reference with all endpoints, schemas, examples
- OpenAPI schema auto-generated from FastAPI

### Template Layer

**Configuration**: `Jinja2Templates` instance in `app/core/templates.py`
- Template directory: `templates/` at project root
- Static files mounted at `/static` in main.py

**Template structure**:
- `base.html` - Base template with blocks (title, content, extra_css, extra_js)
- `templates/*.html` - Page templates using `{% extends "base.html" %}`
- `templates/partials/` - Reusable components via `{% include %}`

**Page routes**: Return `templates.TemplateResponse(template_name, context_dict)`
- Context must include `"request": request` parameter
- Set `include_in_schema=False` to exclude from API docs

**Static files**: Reference with `url_for('static', path='/css/style.css')`

### Admin Interface

**Access**: http://127.0.0.1:8000/admin

**Architecture**: Auto-discovers all `ModelView` subclasses from `app/admin/views.py`
- No manual registration needed - just create view class in `app/admin/views.py`
- Uses `sync_engine` (psycopg2) for database operations

### Testing Infrastructure

**Configuration**:
- `asyncio_mode = "auto"` - No `@pytest.mark.asyncio` needed
- `testpaths = ["tests"]`
- Custom marker: `@pytest.mark.integration` for tests requiring Celery worker

**Test database**: Separate `{POSTGRES_DB}_test` database
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

1. Create SQLModel class in `app/models/your_model.py` with `table=True` and explicit `__tablename__`
2. Generate migration: `make db-migrate message="add your_table"`
3. Apply migration: `make db-upgrade`

### Adding New Service

1. Create service class in `app/services/your_service.py` with business logic
2. Add provider function returning service instance
3. Create type alias: `YourServiceDep = Annotated[YourService, Depends(get_your_service)]`
4. Service auto-exported via `app/services/__init__.py` - no manual import needed

### Adding New API Endpoint

1. Create router in `app/api/your_endpoints.py` with `APIRouter()` instance
2. Include in `app/api/router.py` using `api_router.include_router(your_endpoints.router, tags=["tag"])`
3. Inject service via type alias: `async def endpoint(service: YourServiceDep)`
4. Return SQLModel instances or Pydantic schemas

### Adding Template Page

1. Create HTML template in `templates/your_page.html` extending `base.html`
2. Override blocks: `{% block title %}`, `{% block content %}`
3. Add route in `app/api/pages.py` returning `templates.TemplateResponse("your_page.html", {"request": request})`
4. Set `include_in_schema=False` on route decorator

### Adding Celery Task

1. Create task in `app/tasks/your_tasks.py` with `@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.task_name")`
2. Tasks auto-discovered via glob pattern - no manual import needed
3. Trigger with `task_function.delay(*args)` or `task_function.apply_async()` for advanced options
4. Always use `@celery_app.task` (not `@shared_task`), tasks are synchronous, keep idempotent

### Adding Admin View

Create `ModelView` subclass in `app/admin/views.py` with `model=YourModel` - auto-registered on startup.

### TypeScript Client Generation

Run `make client-generate` to export OpenAPI schema and generate TypeScript client in `./client/` with full type safety (*.ts). SQLModel classes become TypeScript types with full IDE autocomplete.

### Library Testing Pattern

Test library functionality via demo endpoints in `app/api/lib/`:
- **1:1 mapping**: Each library function gets one test endpoint
- **Mirror structure**: `app/lib/langchain/` → `app/api/lib/langchain/`
- **Example**: `app/lib/langchain/llm.py` has `create_chat_model()` and `invoke_model()` → endpoints at `/api/lib/langchain/llm/create-model` and `/api/lib/langchain/llm/invoke`
- Naming convention: Prefix private items with `_` to exclude from exports

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
