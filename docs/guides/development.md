# Development Patterns

A guide to common workflows and coding conventions across the codebase.

---

## Core Principles

### Type Hints & Documentation

Use `Annotated[{Type}, "{description}"]` for input parameters that need explanation. Self-explanatory parameters remain unadorned. Docstrings describe only the function's purpose—omit parameter and return value lists. Return types use standard type hints.

### File Naming

Name related files with consistent prefixes using the pattern `{feature}_{type}.py`, where type indicates file purpose (service, tasks, schemas, etc.). This applies to services, tasks, API endpoints, schemas, and tests. Files sort together alphabetically, making feature boundaries clear and simplifying navigation.

Centralize enums in dedicated `enums.py` files within model directories to prevent circular imports and maintain a single source of truth.

### Package Exports

- **Models, Services, Schemas**: Use explicit imports with `__all__ = ["{Class}"]`
- **Tasks**: Use `auto_import(__file__, "app.tasks")` for Celery registration
- **Private members**: Prefix with `_` to exclude from exports

---

## Database & Models

### Adding a New Model

1. Create a SQLModel class in `app/models/{model}.py` with `table=True` and explicit `__tablename__`
2. Generate migration: `make db-migrate message="add {table}"`
3. Apply migration: `make db-upgrade`

---

## Services & Dependencies

### Adding a New Service

1. Create a class in `app/services/{service}.py` containing business logic
2. Add a provider function that returns a service instance
3. Create a type alias: `{Service}Dep = Annotated[{Service}, Depends(get_{service})]`
4. Export in `__init__.py`: `from .{service} import {Service}, {Service}Dep, get_{service}` and update `__all__`

---

## API Development

### Adding an Endpoint

1. Create an `APIRouter` in `app/api/{endpoints}.py` with route handlers
2. Import `APITag` from `app.core.openapi_tags` for type-safe tag usage
3. Include in `app/api/router.py`: `api_router.include_router({endpoints}.router, tags=[APITag.{TAG}])`
4. Inject services via type alias: `async def endpoint(service: {Service}Dep)`
5. Return SQLModel instances or Pydantic schemas
6. For new tags: define in `APITag` enum and `TAG_METADATA` in `app/core/openapi_tags.py`

### Adding a Template Page

1. Create a template in `templates/{page}.html` extending `base.html`
2. Override blocks: `{% block title %}`, `{% block content %}`
3. Add a route in `app/api/pages.py` returning `templates.TemplateResponse("{page}.html", {"request": request})`
4. Set `include_in_schema=False` on the route decorator

### TypeScript Client Generation

Run `make client-generate` to produce a TypeScript client in `./client/` with full type safety.

---

## Background Processing

### Adding a Celery Task

1. Create a task in `app/tasks/{tasks}.py` with `@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.{task_name}")`
2. Add `auto_import(__file__, "app.tasks")` to `tasks/__init__.py`
3. Trigger with `{task_name}.delay(*args)` or `.apply_async()` for additional options

### Adding an Extension Beat Schedule

1. Create `tasks/schedules.py` in the extension directory with a `SCHEDULES` dictionary
2. Define schedules using `crontab()` expressions from `celery.schedules`
3. Schedule keys are automatically prefixed with the extension name to prevent conflicts

Schedules execute in the timezone configured by `CELERY_TIMEZONE`. No core code changes are needed—schedules are auto-discovered at startup from enabled extensions. View registered schedules in Flower UI or Redis with `redbeat:*` key patterns. Reference `app/extensions/_example/tasks/schedules.py` for format examples.

---

## Admin Interface

### Adding an Admin View

**Basic configuration:**
1. Create a `ModelView` subclass in `app/admin/views.py` with `model={Model}` (auto-registered)
2. Set display name, icon, column lists for list/form/detail pages, search fields, and sortable columns

**File organization:**
Split views into multiple files for maintainability. Structure `admin/views.py` to re-export all view classes from individual files. Auto-discovery scans the module namespace via `inspect.getmembers()`—views imported in `views.py` are automatically registered.

**Column groups:**
Define module-level constants grouping related columns by domain. Use the spread operator to compose configurations from multiple groups for reusability.

**Customization:**
- Add `column_formatters` dict mapping columns to formatting functions
- Use `app/admin/filters.py` for reusable filter base classes
- `EnumFilterBase` auto-generates filter options from enum classes
- Custom filters implement `lookups()` and `async get_filtered_query()` methods, supporting multiple filters that combine via query parameters

---

## Integrations

### Library Integration

**Universal capabilities** require an abstraction layer:

1. Create abstraction in `app/lib/{capability}/`: protocol (`base.py`), enums (`config.py`), factory, and dependencies
2. Implement provider in `app/lib/{library}/{capability}.py` named `{Library}{Capability}Provider`
3. Register by adding an enum value, mapping to the class in factory, and updating settings default
4. Test endpoints: schemas in `app/api/lib/schemas/{capability}.py`, endpoints use DI

**Library-specific features** (no abstraction needed):

1. Implement in `app/lib/{library}/{feature}.py`
2. Optionally add test endpoints in `app/api/lib/{library}/{feature}.py`

Mirror `app/lib/` structure in `app/api/lib/` for testing, with 1:1 endpoint mapping and shared schemas via `app/api/lib/schemas/`.

### External Service Integration

**Directory structure:**

```
app/integrations/{service}/
├── types.py         # TypedDict for external API structures
├── client.py        # Async HTTP client with retry logic
├── dependencies.py  # DI providers
├── webhook.py       # Webhook payload parsing (optional)
└── utils.py         # Formatters and helpers
```

**Implementation steps:**

1. Define TypedDict types for webhook/API structures in `types.py`
2. Create a client class with async methods in `client.py`
3. Add Pydantic schemas in `app/schemas/{service}.py` for endpoint validation
4. Create API endpoints in `app/api/integrations/{service}.py` to trigger actions
5. Create webhook endpoints in `app/api/webhooks/{service}.py` to receive events
6. Add Celery tasks in `app/tasks/{service}_tasks.py` for background processing
7. Implement message formatters in `utils.py` for database storage

**Design principles:**
- TypedDict for external APIs (zero overhead)
- Pydantic for internal endpoints (validation)
- Celery for async webhook processing (fast response times)
- Format rich data for database storage (LLM context)