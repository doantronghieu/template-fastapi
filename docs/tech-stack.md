# Tech Stack

Complete guide to the technologies used in this project.

## Table of Contents

- [Database (SQLModel + Supabase)](#database-sqlmodel--supabase)
- [Task Queue (Celery + Redis Cloud)](#task-queue-celery--redis-cloud)
- [Migrations (Alembic)](#migrations-alembic)
- [API Framework (FastAPI)](#api-framework-fastapi)
- [Admin Interface (SQLAdmin)](#admin-interface-sqladmin)
- [Templates (Jinja2)](#templates-jinja2)
- [Testing (pytest)](#testing-pytest)

---

## Database (SQLModel + Supabase)

**Tech Stack:**
- SQLModel 0.0.22+ - SQL databases with Python type hints (SQLAlchemy + Pydantic)
- SQLAlchemy async - Async database operations via asyncpg driver
- Supabase PostgreSQL - Cloud database with Session Pooler (pgbouncer)

**Implementation:** `app/core/database.py`

### Architecture - Dual Engine Setup

**1. Async Engine (`engine`):**
- Driver: asyncpg (`postgresql+asyncpg://`)
- Usage: FastAPI endpoints via async sessions
- Supabase compatibility: `statement_cache_size=0` for pgbouncer Session Pooler
- Connection URL: `settings.DATABASE_URL` with URL-encoded credentials
- See `app/core/config.py` for URL construction

**2. Sync Engine (`sync_engine`):**
- Driver: psycopg2 (`postgresql+psycopg2://`)
- Usage: SQLAdmin interface (requires sync operations)
- Connection URL: `settings.SYNC_DATABASE_URL` with URL-encoded credentials

### Session Management

- `async_session_maker`: Session factory with `expire_on_commit=False`
- Injection: Use `SessionDep` type alias from `app.dependencies`
- Pattern: `async def endpoint(session: SessionDep)` for clean signatures

### Models

- Location: `app/models/*.py`
- Base: Inherit from `SQLModel` with `table=True`
- Auto-discovery: Alembic auto-imports all models via glob pattern
- See `alembic/env.py` for migration setup

### Initialization

- `init_db()`: Creates all tables at startup via lifespan context manager
- Called from `app/main.py` during application startup

---

## Task Queue (Celery + Redis Cloud)

**Tech Stack:**
- Celery 5.5+ - Distributed task queue for async background jobs
- Redis Cloud - Message broker and result backend
- Redbeat - Redis-based Beat scheduler for periodic tasks
- Flower 2.0+ - Monitoring UI at http://127.0.0.1:5555

**Implementation:** `app/core/celery.py`

### Broker and Backend

- Connection: `REDIS_URL` directly (Redis Cloud free tier supports single database only)
- Max connections: 30 (free tier limit)
- Optimized usage: ~10 connections total (~33% usage)
- See `app/core/config.py` for URL construction

### Task Discovery

- Auto-import from `app/tasks/*.py` via glob pattern in `__init__.py`
- Extension tasks: Auto-loaded via `load_extensions("tasks")`
- Task naming: Use `f"{settings.CELERY_TASKS_MODULE}.task_name"` format

### Beat Scheduler (Periodic Tasks)

- Backend: Redbeat (Redis-based) for schedule persistence across container restarts
- Auto-discovery: Scans extension `tasks/schedules.py` for `SCHEDULES` dictionary
- Key prefixing: Schedule keys automatically prefixed with extension name (e.g., `hotel.daily-task`)
- Timezone: Configured via `CELERY_TIMEZONE` setting
- See extension template: `app/extensions/_example/tasks/schedules.py`

### Task Execution

- Trigger: `task_function.delay(*args)` returns `AsyncResult` with `.id`
- Status: `AsyncResult(task_id, app=celery_app)` provides `.state`, `.result`, `.ready()`
- Monitoring: View tasks in Flower UI or check logs

### Docker Services

- `celery-worker`: Background task execution (pool=solo, concurrency=1)
- `celery-beat`: Periodic task scheduler
- `flower`: Web-based monitoring at http://127.0.0.1:5555
- See `docker-compose.yml` and `Makefile` for infrastructure commands

### Redis Cloud Free Tier Optimization (30 connection limit)

**Target:** <10 connections (~33% usage) to stay below 80% alert threshold

**Connection Budget Breakdown:**
- FastAPI Producer: 2 connections (1 broker + 1 result backend)
- Celery Worker: 3 connections (1 broker + 1 result + 1 worker pool)
- Celery Beat: 3 connections (1 broker + 1 Redbeat scheduler + 1 result)
- Flower: 2 connections (1 broker + 1 result for monitoring)
- **Total:** ~10 connections (leaves 20 connections buffer for spikes)

Configuration uses aggressive connection pooling limits to minimize usage.

### Task ID Context Pattern

- Automatic task ID binding via Celery signals (`task_prerun`/`task_postrun`) in `app/core/celery.py`
- Task ID stored in `ContextVar` in `app/core/celery.py` (co-located with signals)
- Use `get_task_id()` helper in log messages: `logger.info(f"{get_task_id()}Processing...")`
- Task ID prefix format: `[b83caca6]` (first 8 characters)
- No manual wrapping needed - signals handle binding/unbinding automatically

---

## Migrations (Alembic)

**Tech Stack:**
- Alembic 1.14+ - Database migrations with async support
- SQLModel - Metadata source for autogenerate
- asyncpg - Async PostgreSQL driver
- Supabase PostgreSQL - Cloud database target

**Implementation:** `alembic/env.py`

### Auto-Discovery

- Core models: Glob pattern auto-imports from `app/models/*.py`
- Extension models: `load_extensions("models")` imports extension tables
- No manual imports needed - add new model file and migrations detect it automatically

### Async Support

- Uses `create_async_engine()` with asyncpg driver for Supabase
- `run_async_migrations()`: Executes migrations in async context
- Compatible with async database operations

### Supabase Compatibility

- Loads `.env` via `load_dotenv()` for environment variables
- Uses `settings.DATABASE_URL` with URL-encoded credentials
- Disables prepared statement cache (`statement_cache_size=0`) for pgbouncer Session Pooler
- NullPool: No connection pooling during migrations

### Migration Workflow

- Generate: `make db-migrate message="description"`
- Apply: `make db-upgrade`
- Rollback: `make db-downgrade`
- Reset: `make db-reset` (⚠️ deletes all data)

Commands execute: `uv run alembic {command}`

### Autogenerate

- Detects model changes by comparing `SQLModel.metadata` with database schema
- Creates migration scripts in `alembic/versions/`
- Review generated migrations before applying

---

## API Framework (FastAPI)

**Tech Stack:**
- FastAPI 0.118+ - Modern async web framework with OpenAPI auto-generation
- Scalar - API documentation UI (mounted at `/scalar`)
- CORS middleware - Cross-origin resource sharing configuration
- Static files - Mounted at `/static` from project root

**Implementation:** `app/main.py`

### Architecture

- **Lifespan context manager:** Initializes database tables and message handlers on startup
- **OpenAPI customization:** Auto-discovers extension tags and creates nested navigation via x-tagGroups
- **Router aggregation:** Core API routes at `/api`, page routes for templates, admin at `/admin`
- **Middleware:** CORS configured for all origins (adjust for production)

### API Documentation

- Scalar UI at http://127.0.0.1:8000/scalar with nested navigation
- Type-safe tags: Use `APITag` enum from `app/core/openapi_tags.py`
- OpenAPI schema auto-generated from route definitions
- See `app/core/openapi_tags.py` for tag management system

---

## Admin Interface (SQLAdmin)

**Tech Stack:**
- SQLAdmin 0.20+ - Admin interface for database management
- Jinja2 - Template engine for admin UI customization
- SQLAlchemy (sync) - Database operations via `sync_engine`

**Implementation:** `app/core/admin.py`

### Access

http://127.0.0.1:8000/admin

### Auto-Discovery Pattern

- Core admin: Scans `app.admin.views` module namespace for `ModelView` subclasses
- Extension admin: Each extension's `setup_admin()` scans its `admin.views` module
- No manual registration - views imported into namespace are auto-registered
- Uses `inspect.getmembers()` to find `ModelView` subclasses

### Template Loading

- ChoiceLoader: Searches extension templates before falling back to SQLAdmin defaults
- Extensions can override templates by placing files in their `templates/` directory
- Search order: Extension templates → Core templates → SQLAdmin built-ins

### Database Engine

- Uses `sync_engine` (psycopg2 driver) from `app/core/database`
- SQLAdmin requires synchronous operations (not compatible with async)

### Admin Views

- Location: `app/admin/views.py` for core models
- Base class: `sqladmin.ModelView`
- Configuration: Set `model`, `name`, `icon`, `column_list`, `column_details_list`, etc.
- Reusable filters: See `app/admin/filters.py` for `EnumFilterBase` and custom filter utilities

---

## Templates (Jinja2)

**Tech Stack:**
- Jinja2 3.1+ - Server-side templating engine
- FastAPI Jinja2Templates - Integration with FastAPI

**Implementation:** `app/core/templates.py`

### Architecture

- `BASE_DIR`: Project root directory
- `TEMPLATES_DIR`: `templates/` directory at project root
- `templates`: Jinja2Templates instance for rendering

### Template Structure

- `templates/base.html` - Base template with blocks (`title`, `content`, `extra_css`, `extra_js`)
- `templates/*.html` - Page templates using `{% extends "base.html" %}`
- `templates/partials/` - Reusable components via `{% include %}`

### Usage in Page Routes

- Import: `from app.core.templates import templates`
- Return: `templates.TemplateResponse(template_name, {"request": request, ...})`
- Static files: Reference with `url_for('static', path='/css/style.css')`
- Exclude from API docs: Set `include_in_schema=False` on route decorator

See `app/api/pages.py` for page route implementations.

---

## Testing (pytest)

**Tech Stack:**
- pytest 8.3+ - Testing framework
- pytest-asyncio - Async test support (`asyncio_mode="auto"` in `pyproject.toml`)
- httpx - Async HTTP client for API testing
- Supabase PostgreSQL - Test database (`{POSTGRES_DB}_test`)

**Implementation:** `tests/conftest.py`

### Test Database

- Name: `{POSTGRES_DB}_test` (e.g., `postgres_test` on Supabase)
- Creation: Auto-created at session start if doesn't exist
- Tables: Created once per session via `SQLModel.metadata.create_all`
- Cleanup: Tables dropped at session end
- Connection: Uses same Supabase credentials as development (`.env` file)

### Isolation Strategy

- Each test runs in a transaction that rolls back after completion
- Provides full isolation without recreating tables between tests
- Fast test execution with proper data isolation

### Fixtures (all function-scoped except `test_engine`)

**1. `test_engine` (session scope):**
- Async database engine with NullPool
- Creates test database and tables at session start
- Drops tables at session end
- Auto-used by `db_session` fixture

**2. `db_session` (function scope):**
- Async session with transaction rollback for isolation
- Each test gets fresh session that rolls back after completion
- Use for database operations in tests

**3. `client` (function scope):**
- Async HTTP client (`httpx.AsyncClient`) with database override
- Automatically overrides `get_session` dependency to use test session
- Use for API endpoint testing
- Clears dependency overrides after test

**4. `sync_client` (function scope):**
- Synchronous TestClient for non-async tests
- No database override (use for simple non-DB tests)

### Extension Support

- `ENABLED_EXTENSIONS` set to `"_example"` for testing
- Enables extension models/routes during test execution

### Configuration

See `pyproject.toml` for pytest configuration (`asyncio_mode`, `testpaths`, `markers`).
See `tests/README.md` for detailed usage guide and examples.
