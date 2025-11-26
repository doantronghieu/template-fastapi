# Development Patterns

This document describes common development workflows and coding patterns.

## Type Hints & Documentation

**Principle**: Replace docstring parameter descriptions with `Annotated[Type, "description"]`. Self-explanatory parameters stay clean. Docstrings describe only function purpose—no param/return lists.

**Applies to**: Input parameters. Returns use standard type hints.

## File Naming Conventions

**Principle**: Name related files using consistent prefixes for discoverability and maintainability.

**Feature-based naming**:
- Use shared prefix matching the feature or domain name
- Apply pattern `{feature}_{type}.py` where type indicates file purpose (service, tasks, schemas, etc.)
- Applies to: services, tasks, API endpoints, schemas, test, etc. files
- Files sort together alphabetically, making feature boundaries clear

**Benefits**:
- Quick visual grouping in file explorers
- Immediate understanding of feature scope
- Simplified navigation and refactoring
- Clear boundaries between different features

**Enum organization**:
- Centralize enums in dedicated `enums.py` within model directories
- Prevents circular import issues
- Provides single source of truth for type definitions

## Adding New Model

1. Create SQLModel class in `app/models/your_model.py` with `table=True` and explicit `__tablename__`
2. Generate migration: `make db-migrate message="add your_table"`
3. Apply migration: `make db-upgrade`

## Adding New Service
- Create class in `app/services/your_service.py` with business logic
- Add provider function returning service instance
- Create type alias: `YourServiceDep = Annotated[YourService, Depends(get_your_service)]`
- Export in `__init__.py`: `from .your_service import YourService, YourServiceDep, get_service` + `__all__` list

## Adding New API Endpoint
- Create `APIRouter` in `app/api/your_endpoints.py` with route handlers
- Import `APITag` from `app.core.openapi_tags` for type-safe tag usage
- Include in `app/api/router.py`: `api_router.include_router(your_endpoints.router, tags=[APITag.YOUR_TAG])`
- Inject services via type alias: `async def endpoint(service: YourServiceDep)`
- Return SQLModel instances or Pydantic schemas
- If adding new tag: Define in `APITag` enum and `TAG_METADATA` in `app/core/openapi_tags.py`

## Adding Template Page
- Create template in `templates/your_page.html` extending `base.html`
- Override blocks: `{% block title %}`, `{% block content %}`
- Add route in `app/api/pages.py` returning `templates.TemplateResponse("your_page.html", {"request": request})`
- Set `include_in_schema=False` on route decorator

## Adding Celery Task
- Create task in `app/tasks/your_tasks.py` with `@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.task_name")`
- Add `auto_import(__file__, "app.tasks")` to `tasks/__init__.py`
- Trigger: `task_function.delay(*args)` or `.apply_async()` for options

## Adding Extension Beat Schedule
- Create `tasks/schedules.py` in extension directory with `SCHEDULES` dictionary
- Define schedules using `crontab()` expressions from `celery.schedules`
- Schedule keys automatically prefixed with extension name to prevent conflicts (e.g., `hotel.daily-task`)
- Schedules execute in timezone configured by `CELERY_TIMEZONE` setting
- No core code changes needed - auto-discovered at startup from enabled extensions
- View registered schedules in Flower UI or Redis with `redbeat:*` key pattern
- Reference template in `app/extensions/_example/tasks/schedules.py` for format examples

## Adding Admin View

**Basic configuration:**
- Create `ModelView` subclass in `app/admin/views.py` with `model=YourModel` - auto-registered
- Set display name, icon, column lists for list/form/detail pages, search fields, sortable columns

**File organization:**
- Split into multiple files for better maintainability
- Structure: `admin/views.py` re-exports all view classes from individual files
- Auto-discovery scans module namespace via `inspect.getmembers()` - views imported in `views.py` are automatically registered

**Column groups for reusability:**
- Define module-level constants grouping related columns by domain
- Use spread operator to compose configurations from multiple groups
- Enables single source of truth, reduces duplication, provides clear semantic organization

**Display formatters:**
- Add `column_formatters` dict mapping columns to formatting functions

**Custom filters:**
- Use `app/admin/filters.py` module for reusable filter base classes
- `EnumFilterBase` automatically generates filter options from enum classes
- Custom filters implement `lookups()` and `async get_filtered_query()` methods
- Supports multiple filters combining with query parameters

## Package Exports
- **Models/Services/Schemas**: Explicit imports + `__all__ = ["YourClass"]`
- **Tasks**: `auto_import(__file__, "app.tasks")` for Celery registration
- **Private**: Prefix with `_` to exclude

## TypeScript Client
- Run `make client-generate` for TypeScript client in `./client/` with full type safety

## Adding Library Integration

**Universal capabilities** (create abstraction):
1. Abstraction layer in `app/lib/{capability}/`: protocol (base.py), enums (config.py), factory, dependencies
2. Provider implementation in `app/lib/{library}/{capability}.py` named `{Library}{Capability}Provider`
3. Register: add enum value, map to class in factory, update settings default
4. Test endpoints: schemas in `app/api/lib/schemas/{capability}.py`, endpoints use DI

**Library-specific features** (no abstraction):
1. Implementation in `app/lib/{library}/{feature}.py`
2. Optional test endpoints in `app/api/lib/{library}/{feature}.py`

**Testing pattern**: Mirror `app/lib/` structure in `app/api/lib/` with 1:1 endpoint mapping, share schemas via `app/api/lib/schemas/`

## Adding External Integration

**Directory structure** for third-party services (Messenger, Slack, Twilio):
```
app/integrations/{service}/
├── types.py         # TypedDict for external API structures
├── client.py        # Async HTTP client with retry logic
├── dependencies.py  # DI providers
├── webhook.py       # Webhook payload parsing (optional)
└── utils.py         # Formatters and helpers
```

**Implementation steps**:
1. TypedDict types for webhook/API structures in `types.py`
2. Client class with async methods in `client.py`
3. Pydantic schemas in `app/schemas/{service}.py` for endpoint validation
4. API endpoints in `app/api/integrations/{service}.py` to trigger actions
5. Webhook endpoints in `app/api/webhooks/{service}.py` to receive events
6. Celery tasks in `app/tasks/{service}_tasks.py` for background processing
7. Message formatters in `utils.py` for database storage

**Principles**: TypedDict for external APIs (zero overhead), Pydantic for our endpoints (validation), Celery for async webhook processing (response time requirements), format rich data for database storage (LLM context).
