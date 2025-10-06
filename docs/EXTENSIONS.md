# Extension System Guide

Modular extension system for custom features without affecting core codebase.

## Quick Start

### 1. Create Extension from Template

```bash
# Copy template
cp -r app/extensions/_example app/extensions/my_extension

# Enable in .env
echo "ENABLED_EXTENSIONS=my_extension" >> .env
```

### 2. Update Extension

```python
# app/extensions/my_extension/__init__.py
# Update setup_*() functions and router prefixes

# app/extensions/my_extension/models/feature.py
# Rename tables with prefix: my_extension_tablename
```

### 3. Generate Database Migrations

```bash
make db-migrate message="add my_extension extension"
make db-upgrade
```

### 4. Run Tests

```bash
# Copy test template
cp -r tests/extensions/_example tests/extensions/my_extension

# Run extension tests
pytest tests/extensions/my_extension/
```

---

## Architecture Rules

### ✅ Allowed

- Extensions import from core: `from app.models import User`
- Extensions extend core models via foreign keys
- Extensions add new API endpoints, tasks, admin views

### ❌ Forbidden

- Core importing extensions: `from app.extensions.my_extension import ...`
- Extensions importing other extensions
- Extension table names without prefix (must be `{extension}_tablename`)

---

## Directory Structure

```
app/extensions/my_extension/
├── __init__.py         # Extension entry point (setup_*() functions)
├── models/             # Database models (prefix tables!)
├── schemas/            # Pydantic schemas
├── services/           # Business logic
├── tasks/              # Celery background tasks
├── api/                # API endpoints
│   └── router.py       # Route aggregator
└── admin/              # Admin interface views
    └── views.py
```

---

## Configuration

### Environment Variables

```bash
# .env
ENABLED_EXTENSIONS=                  # Core only (default)
ENABLED_EXTENSIONS=extension_a          # Single extension
ENABLED_EXTENSIONS=extension_a,extension_b # Multiple extensions
```

### Per-Environment Deployment

```bash
# Production - Extension A
ENABLED_EXTENSIONS=extension_a

# Production - Extension B
ENABLED_EXTENSIONS=extension_b

# Development - All extensions
ENABLED_EXTENSIONS=extension_a,extension_b,extension_c
```

---

## Development Workflow

### Creating Models
- Create SQLModel class with `table=True` in `models/feature.py`
- Set `__tablename__ = "{extension_name}_tablename"` (must prefix!)
- Import core models if needed: `from app.models import User`
- Export in `models/__init__.py`: `from .feature import MyModel` + `__all__ = ["MyModel"]`

### Creating Services
- Create service class in `services/feature_service.py` with `__init__(self, session: AsyncSession)`
- Add business logic methods (async CRUD operations)
- Create provider function: `def get_service(session: SessionDep) -> MyService`
- Create type alias: `MyServiceDep = Annotated[MyService, Depends(get_service)]`
- Export in `services/__init__.py` with explicit imports and `__all__` list

### Creating API Endpoints
- Create `APIRouter()` in `api/feature.py` with route handlers
- Inject services via type alias: `async def endpoint(service: MyServiceDep)`
- Aggregate routes in `api/router.py` using `router.include_router()`

### Creating Tasks
- Create task function with `@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.task_name")`
- Add `auto_import(__file__, "app.extensions.{name}.tasks")` to `tasks/__init__.py`

### Creating Admin Views
- Create `ModelView` subclass in `admin/views.py` with `model=YourModel`
- Set `name`, `icon`, `column_list` attributes for admin interface

---

## Testing

### Test Structure
- Create `tests/extensions/{extension_name}/` directory
- Add `test_api.py`, `test_models.py`, `test_services.py`, `test_tasks.py`
- Use `async def` for all test functions with AsyncClient
- Extension enabled in `tests/conftest.py` via `os.environ.setdefault("ENABLED_EXTENSIONS", "_example")`

---

## Deployment

### Docker Build
- Add `ARG ENABLED_EXTENSIONS=""` and `ENV ENABLED_EXTENSIONS=${ENABLED_EXTENSIONS}` to Dockerfile
- Build per extension: `docker build -t app-ext-a --build-arg ENABLED_EXTENSIONS=extension_a .`
- Or use runtime config via `.env` file

---

## Troubleshooting

### Extension Not Loading
- Check `ENABLED_EXTENSIONS` in `.env` (comma-separated, no spaces)
- Verify `setup_*()` functions exist in extension `__init__.py`
- Check logs for import errors
- Ensure table names prefixed with `{extension_name}_`

### Migration Issues
- Run migrations with same `ENABLED_EXTENSIONS` as deployment
- Regenerate: `ENABLED_EXTENSIONS=my_extension make db-migrate message="fix extension"`

### Import Errors
- ✅ Extensions → Core: Allowed
- ❌ Core → Extensions: Refactor to core
- ❌ Extension → Extension: Move shared code to core

---

## Best Practices

1. **Table naming**: Always prefix with `{extension_name}_`
2. **Self-contained**: Extensions should not depend on each other
3. **Test coverage**: Write tests for all extension features
4. **Documentation**: Document extension-specific behavior
5. **Migration discipline**: Always run migrations with same `ENABLED_EXTENSIONS` as deployment
