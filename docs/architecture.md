# Application Architecture

Overview of application structure, component organization, and dependency injection.

## Architecture Documentation

| Document | Authoritative For |
|----------|-------------------|
| [Module Structure](architecture/module-structure.md) | Directory layout, dependency rules, design guidelines |
| [Auto-Discovery System](architecture/autodiscover-system.md) | File conventions, URL patterns, discovery models, templates |

## Application Structure

**Core application files:**

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app with lifespan, static files, routes |
| `app/core/config.py` | Pydantic BaseSettings, `.env` loading |
| `app/core/database.py` | Dual engine (async/sync), session factory |
| `app/core/autodiscover.py` | Convention-based module registration |
| `app/core/celery.py` | Celery app, Redis broker, task ID context |
| `app/core/admin.py` | SQLAdmin with auto-discovery |
| `app/core/templates.py` | Jinja2Templates instance |
| `app/core/openapi_tags.py` | Type-safe API tag registry |

**Root-level directories:**

| Directory | Purpose |
|-----------|---------|
| `app/features/` | Vertical slices |
| `app/lib/` | Provider-agnostic abstractions |
| `app/integrations/` | External API clients |
| `app/extensions/` | Optional modules (opt-in) |
| `app/models/` | Shared SQLModel tables |
| `app/schemas/` | Shared Pydantic schemas |
| `app/services/` | Cross-cutting business logic |
| `app/tasks/` | Core Celery tasks |
| `app/dependencies/` | Shared FastAPI dependencies |
| `app/utils/` | Pure utility functions |
| `templates/` | Global Jinja2 templates |
| `static/` | CSS, JavaScript, images |
| `tests/` | Pytest suite |
| `alembic/` | Database migrations |

## Configuration System

Pydantic BaseSettings loading from `.env` file.

**Implementation:** `app/core/config.py`

| Pattern | Example |
|---------|---------|
| Field definitions | `FIELD: type = Field(default, description="...")` |
| Dynamic properties | `DATABASE_URL`, `SYNC_DATABASE_URL`, `CELERY_BROKER_URL` |
| URL encoding | Credentials with special characters |

**Usage:** Import `settings` singleton → `from app.core.config import settings`

## Dependency Injection

Type alias pattern for clean endpoint signatures.

**Pattern:**
```python
# Definition (in service or dependencies file)
def get_{service}() -> {Service}:
    return {Service}()

{Service}Dep = Annotated[{Service}, Depends(get_{service})]

# Usage (in router)
async def endpoint(service: {Service}Dep):
    return await service.do_something()
```

**Organization:**

| Location | Purpose |
|----------|---------|
| `app/dependencies/core.py` | Core infrastructure |
| `app/dependencies/api.py` | API-layer dependencies |
| `app/services/{service}.py` | Service-specific providers |
| `app/lib/{capability}/dependencies.py` | Library-specific providers |
| `app/features/{feature}/dependencies.py` | Feature-specific providers |

**Benefits:**
- Clean endpoint signatures via type aliases
- Testable via FastAPI dependency overrides
- Lazy instantiation

## Key Components

| Component | Location | Details |
|-----------|----------|---------|
| Configuration | `app/core/config.py` | Pydantic BaseSettings, `.env` loading |
| Database | `app/core/database.py` | Dual engine (async/sync), Supabase PostgreSQL |
| Auto-Discovery | `app/core/autodiscover.py` | Convention-based registration |
| Task Queue | `app/core/celery.py` | Celery with Redis Cloud, auto-discovered tasks/schedules |
| API Entry | `app/main.py` | FastAPI app, Scalar UI at `/scalar`, SQLAdmin at `/admin` |
| Templates | `app/core/templates.py` | Jinja2Templates instance |
| Admin | `app/core/admin.py` | SQLAdmin with ModelView auto-discovery |
| Migrations | `alembic/env.py` | Async Alembic with model auto-import |

**Technology details:** See `docs/tech-stack.md` for database, Celery, Alembic, testing configuration.
