# Application Architecture

This document describes the application structure and component organization.

## Application Structure

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
- `app/core/openapi_tags.py` - Type-safe tag registry for API documentation
- `app/core/templates.py` - Jinja2Templates instance with directory configuration
- `app/core/admin.py` - SQLAdmin configuration with auto-discovery
- `app/core/celery.py` - Celery app configuration
- `app/models/` - SQLModel table definitions (auto-imported by Alembic)
- `app/schemas/` - Pydantic request/response schemas
- `app/services/` - Business logic layer with auto-discovery
- `app/tasks/` - Celery task definitions
- `app/admin/` - SQLAdmin views and reusable filter utilities (auto-registered)

**Supporting directories:**
- `templates/` - Jinja2 templates (base.html, pages, partials)
- `static/` - CSS, JavaScript, images
- `tests/` - Pytest suite with async support and fixtures
- `alembic/` - Database migrations with async support
- `docker/` - Docker configurations (Dockerfile.celery)
- `scripts/` - Utility scripts (export_openapi.py)
- `docs/` - Documentation
- `app/extensions/` - Extension modules (optional, loaded via config)

## Configuration System

Pydantic BaseSettings loading from `.env` file. Use `.env.example` as template.

**Implementation:** `app/core/config.py`
- Field definitions with descriptions
- Dynamic properties: `DATABASE_URL`, `SYNC_DATABASE_URL`, `CELERY_BROKER_URL`, etc.
- URL encoding for credentials

## Database Layer

Dual engine setup (async for FastAPI, sync for SQLAdmin) with Supabase PostgreSQL.

**See `docs/tech-stack.md`** for database configuration details (engines, sessions, models, initialization).

**Implementation:** `app/core/database.py`
**Models:** `app/models/*.py` (inherit from SQLModel with `table=True`)

## Dependency Injection

Type alias pattern for clean endpoint signatures: `ServiceDep = Annotated[Service, Depends(get_service)]`

**Organization**:
- Core dependencies: `app/core/dependencies.py` (sessions, settings)
- Service layer: `app/services/*.py` (business logic with auto-discovery)
- Library dependencies: `app/lib/{library}/dependencies.py` (co-located)

**Pattern**: Inject via type aliases → `async def endpoint(service: ServiceDep)`

## Alembic Migrations

Auto-discovers models from `app/models/*.py` and extensions. Async-compatible with Supabase.

**See `docs/tech-stack.md`** for Alembic configuration and migration workflow details.

**Implementation:** `alembic/env.py`
**Commands**: `make db-migrate message="..."`, `make db-upgrade`, `make db-downgrade`, `make db-reset`

## Celery Task Queue

Distributed task queue with Redis Cloud broker/backend and Redbeat scheduler.

**See `docs/tech-stack.md`** for Celery configuration, connection optimization, and task execution details.

**Implementation:** `app/core/celery.py`
**Usage**: Trigger tasks with `.delay()`, monitor at http://127.0.0.1:5555 (Flower)
**Docker**: `make infra-up` starts celery-worker, celery-beat, flower

## API Layer

Router aggregation at `/api` prefix with type-safe tag management.

**See `docs/tech-stack.md`** for FastAPI and API documentation details.

**Endpoint pattern**:
- Create `APIRouter()` at module level
- Inject services via type aliases: `async def endpoint(service: ServiceDep)`
- Return SQLModel/Pydantic instances (auto-serialized)
- Business logic in service layer

**Scalar UI**: http://127.0.0.1:8000/scalar
**Tags**: Use `APITag` enum from `app/core/openapi_tags.py`

## Template Layer

Jinja2 templates for server-side rendering.

**See `docs/tech-stack.md`** for Jinja2 configuration and template structure details.

**Implementation:** `app/core/templates.py`
**Routes:** `app/api/pages.py` (returns `templates.TemplateResponse(...)`)

## Admin Interface

SQLAdmin interface at http://127.0.0.1:8000/admin with auto-discovery of ModelView classes.

**See `docs/tech-stack.md`** for SQLAdmin auto-discovery and configuration details.

**Implementation:** `app/core/admin.py`
**Views:** Create `ModelView` subclasses in `app/admin/views.py` (auto-registered)
**Filters:** Reusable utilities in `app/admin/filters.py`

## Testing Infrastructure

pytest with async support and Supabase test database.

**See `docs/tech-stack.md`** for pytest configuration, fixtures, and test database details.
**See `tests/README.md`** for usage guide, examples, and REST Client testing.

**Implementation:** `tests/conftest.py`
**Test DB:** `{POSTGRES_DB}_test` on Supabase (transaction rollback isolation)
**Commands**: `make test`, `pytest -v`, etc.
