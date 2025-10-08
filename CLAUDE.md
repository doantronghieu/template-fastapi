# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI template with SQLModel (async SQLAlchemy), PostgreSQL, Redis, Celery task queue, API documentation via Scalar, and modular extension system for specific customizations. Uses `uv` for dependency management and Docker Compose for infrastructure.

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
- `app/core/openapi_tags.py` - Type-safe tag registry for API documentation
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
- `docs/` - Documentation (EXTENSIONS.md)
- `app/extensions/` - Extension modules (optional, loaded via config)

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

**Core dependencies** in `app/core/dependencies.py`:
- Database sessions, settings, core app concerns only

**Service layer pattern** in `app/services/`:
- Service classes encapsulate business logic
- Provider functions return service instances
- Type aliases for injection: `ServiceDep = Annotated[Service, Depends(get_service)]`
- Auto-discovery: All services automatically imported via `__init__.py`

**Library dependencies** co-located with libraries:
- Each library manages its own dependencies in `app/lib/{library}/dependencies.py`
- Keeps library concerns separate from core app concerns

**Endpoint pattern**: Inject via type aliases for clean signatures

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
- Scalar UI at http://127.0.0.1:8000/scalar with nested navigation via x-tagGroups
- Interactive API reference with all endpoints, schemas, examples
- OpenAPI schema auto-generated from FastAPI
- Centralized tag management in `app/core/openapi_tags.py` for type safety

**Tag Management System**:
- Single source of truth: `TagGroup` enum and `APITag` enum
- Tag metadata maps each tag to description and group assignment
- Auto-generation: `get_openapi_tags()` creates tag metadata, `get_tag_groups()` creates x-tagGroups
- Type-safe usage: Import `APITag` in routers, use `tags=[APITag.HEALTH]` instead of string literals
- Adding new tag: Add enum value + metadata entry (2 lines total) in `app/core/openapi_tags.py`
- Prevents typos, enables IDE autocomplete, eliminates repetition across files

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

## Extension System

Modular architecture for custom features without affecting core codebase.

**Full Documentation**: See `docs/EXTENSIONS.md` for complete guide.

**Quick Start:**
- Template: `app/extensions/_example/`
- Enable: `ENABLED_EXTENSIONS=extension_a` in `.env`
- Create: `cp -r app/extensions/_example app/extensions/my_extension`

**Key Rules:**
- Extensions → Core: ✅ | Core → Extensions: ❌ | Extension → Extension: ❌
- Tables must be prefixed: `{extension_name}_tablename`

## Library Architecture Pattern

Organization strategy for integrating third-party libraries with pluggable provider support via the Strategy pattern.

### Universal vs Library-Specific Architecture

**Decision criteria for abstraction layers:**

Create abstraction in `app/lib/{capability}/` when:
- Multiple providers offer same functionality (LLM, embeddings, etc.)
- Runtime provider switching needed via configuration
- Interface relatively standardized across providers
- Business logic should be provider-agnostic

Keep in library directory `app/lib/{library}/` when:
- Feature unique to one library (chains, agents, retrievers, etc.)
- No equivalent functionality in other providers
- Tightly coupled to library-specific patterns
- Abstraction would be premature or forced

**Directory structure:**
```
app/lib/
├── {capability}/             # Abstraction: base.py (Protocol), config.py (enums),
│                             # factory.py (selection), dependencies.py (DI)
└── {library}/                # Implementation: {capability}.py (provider class),
                              # {feature}.py (library-specific), dependencies.py
```

Avoid deep nesting (`app/lib/ai/llm/`) - use flat structure with clear capability names.

### Provider Implementation Pattern

**Interface and naming:**
- Define interface using `Protocol` or `ABC` in `base.py`
- Name providers specifically: `{Library}{Capability}Provider` (e.g., `LangChainLLMProvider`)
- Each library implements protocol in its own directory
- Avoids generic names, enables multiple capabilities per library

**Factory with type-safe configuration:**
- Create provider type enum in config (e.g., `LLMProviderType`)
- Factory maps enum values to provider classes for runtime selection
- Settings import enum and use `.value` for defaults
- Ensures consistency, prevents typos, validates at startup

**Dependency injection:**
- Co-locate: library deps in `app/lib/{library}/dependencies.py`, core deps in `app/core/dependencies.py`
- Pattern: provider function returns instance, type alias for injection via `Annotated[Type, Depends(fn)]`
- Use `TYPE_CHECKING` guard to avoid circular imports
- Inject in endpoints via type alias parameter for clean signatures

### Test Schema Organization

**Separation strategy:**
- Domain/business schemas: `app/schemas/` for production endpoints
- Library test schemas: `app/api/lib/schemas/{capability}.py` for testing
- Use directory (not single file) organized by capability
- Share schemas across related test endpoints to avoid duplication

## Schema and Model Patterns

### SQLModel Base Pattern ("Fat Models")

**Principle**: Single source of truth for field definitions with descriptions in base classes.

- **Domain model bases** define core business fields with Field descriptions
  - Create base class inheriting from `SQLModel` with shared fields
  - Located in `app/models/` alongside table models
  - Table model inherits from base with `table=True` parameter
  - Response schemas inherit from same base for field reuse
- **Schema-specific bases** define API/request-specific concerns
  - Co-located with schemas in same file for discoverability
  - Used only by request/response schemas, never by table models
  - Group related optional parameters (e.g., external channel fields, internal UUID fields)

### Multiple Inheritance for Schema Composition

**Principle**: Compose schemas from multiple base classes (similar to Zod's `.merge()` or TypeScript intersection types).

- Inherit from multiple base classes to combine different field groups
- Python MRO (Method Resolution Order) applies left-to-right priority for conflicts
- Enables maximum reusability through composition
- Separate concerns: domain fields, API-specific fields, internal fields, authentication fields
- Request schemas combine all necessary bases without field redefinition

### Field Validators Over Redefinition

**Principle**: Add validation without duplicating field definitions using Pydantic decorators.

- Use `@field_validator("field_name")` decorator to add validation to inherited fields
- Use `@model_validator(mode="after")` for cross-field validation logic
- Avoid redefining fields in child schemas unless adding new constraints
- Similar to Zod's `.refine()` method - extend behavior without duplication
- Validator method receives value, performs checks, raises ValueError or returns processed value

### Field Override Guidelines

**Principle**: Only override inherited fields when adding database-specific configurations.

- **Override when needed**: Adding `index=True`, `unique=True`, `sa_column=Column(...)`, etc. or relationship configs
- **Don't override unnecessarily**: If field definition is identical to parent, don't redefine
- **Always add inline comment**: Explain why override is needed (e.g., "# Override to add unique constraint")
- **Accept trade-off**: Field descriptions may be lost when overriding (SQLModel limitation)

### POST Method for Complex Queries

**Principle**: Use POST with request body (instead of GET with query params) to enable schema-level validation.

- **Problem**: GET with `Depends()` instantiates schema with default None values before validation
- **Solution**: Use POST method with request body parameter (no `Depends()`)
- **Benefit**: Pydantic validators run on complete payload, enabling `@model_validator` cross-field checks
- **Documentation**: Add note in endpoint docstring explaining POST usage for validation
- **Pattern**: Common for complex query endpoints requiring "at least one of" logic

### Schema Validation Best Practices

**Validation Location Priority**:
1. **Pydantic `@field_validator`** - Single-field validation rules (preferred)
2. **Pydantic `@model_validator`** - Cross-field validation (requires POST request body)
3. **API layer** - Only when Pydantic validation isn't feasible

**When validation must stay at API layer**:
- GET endpoints with query parameters using `Depends()` (can't use `@model_validator`)
- Complex business logic requiring database queries or external service calls
- Always add inline comment explaining why validation is at API layer

### Base Class Organization

**Co-location Strategy**:
- **Domain bases with models**: Keep base classes in same file as table models (`app/models/`)
  - Reason: Domain-specific, used by table models and response schemas
  - Example: Entity base next to entity table definition
- **Schema bases with schemas**: Keep API-specific bases in same file as request/response schemas (`app/schemas/`)
  - Reason: Only used by API schemas, not domain models
  - Example: Query parameter bases, external integration bases
  - Improves discoverability when working on API layer

**Avoid**: Creating separate `bases.py` files unless bases are truly shared across many unrelated modules.

## Development Patterns

### Adding New Model

1. Create SQLModel class in `app/models/your_model.py` with `table=True` and explicit `__tablename__`
2. Generate migration: `make db-migrate message="add your_table"`
3. Apply migration: `make db-upgrade`

### Adding New Service
- Create class in `app/services/your_service.py` with business logic
- Add provider function returning service instance
- Create type alias: `YourServiceDep = Annotated[YourService, Depends(get_your_service)]`
- Export in `__init__.py`: `from .your_service import YourService, YourServiceDep, get_service` + `__all__` list

### Adding New API Endpoint
- Create `APIRouter` in `app/api/your_endpoints.py` with route handlers
- Import `APITag` from `app.core.openapi_tags` for type-safe tag usage
- Include in `app/api/router.py`: `api_router.include_router(your_endpoints.router, tags=[APITag.YOUR_TAG])`
- Inject services via type alias: `async def endpoint(service: YourServiceDep)`
- Return SQLModel instances or Pydantic schemas
- If adding new tag: Define in `APITag` enum and `TAG_METADATA` in `app/core/openapi_tags.py`

### Adding Template Page
- Create template in `templates/your_page.html` extending `base.html`
- Override blocks: `{% block title %}`, `{% block content %}`
- Add route in `app/api/pages.py` returning `templates.TemplateResponse("your_page.html", {"request": request})`
- Set `include_in_schema=False` on route decorator

### Adding Celery Task
- Create task in `app/tasks/your_tasks.py` with `@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.task_name")`
- Add `auto_import(__file__, "app.tasks")` to `tasks/__init__.py`
- Trigger: `task_function.delay(*args)` or `.apply_async()` for options

### Adding Admin View
- Create `ModelView` subclass in `app/admin/views.py` with `model=YourModel` - auto-registered

### Package Exports
- **Models/Services/Schemas**: Explicit imports + `__all__ = ["YourClass"]`
- **Tasks**: `auto_import(__file__, "app.tasks")` for Celery registration
- **Private**: Prefix with `_` to exclude

### TypeScript Client
- Run `make client-generate` for TypeScript client in `./client/` with full type safety

### Adding Library Integration

**Universal capabilities** (create abstraction):
1. Abstraction layer in `app/lib/{capability}/`: protocol (base.py), enums (config.py), factory, dependencies
2. Provider implementation in `app/lib/{library}/{capability}.py` named `{Library}{Capability}Provider`
3. Register: add enum value, map to class in factory, update settings default
4. Test endpoints: schemas in `app/api/lib/schemas/{capability}.py`, endpoints use DI

**Library-specific features** (no abstraction):
1. Implementation in `app/lib/{library}/{feature}.py`
2. Optional test endpoints in `app/api/lib/{library}/{feature}.py`

**Testing pattern**: Mirror `app/lib/` structure in `app/api/lib/` with 1:1 endpoint mapping, share schemas via `app/api/lib/schemas/`

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
