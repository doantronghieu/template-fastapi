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

# app/extensions/my_extension/config.py (optional)
# Add extension-specific settings if needed

# app/extensions/my_extension/models/feature.py
# Rename tables with prefix: my_extension_tablename
```

**Note**: Edit auto-generated `.env.my_extension` in project root.

### 3. Generate Database Migrations

```bash
make db-migrate message="add my_extension extension"
make db-upgrade
```

### 4. Run Tests

```bash
# Run extension tests
pytest tests/extensions/my_extension/
```

---

## Extension Configuration

Extensions can have their own configuration using Pydantic Settings with separate `.env` files. The system **auto-detects** the extension folder name and **auto-generates** the `.env` file by introspecting your Settings class.

### Creating Extension Config

```python
# app/extensions/my_extension/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.extensions import generate_extension_env, get_extension_env_path

class MyExtensionSettings(BaseSettings):
    MY_API_KEY: str = Field(default="", description="API key for service")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=get_extension_env_path(__file__),
        extra="allow",
    )

generate_extension_env(__file__, MyExtensionSettings)
extension_settings = MyExtensionSettings()
```

Auto-generates `.env.{extension_name}` in project root with `KEY=` (empty values). Fill in values manually.

### Using Extension Config

```python
from .config import extension_settings

api_key = extension_settings.MY_API_KEY
```

### Environment File (Auto-Generated)

Auto-generated in project root: `.env.my_extension`

```bash
# MY_EXTENSION Extension Configuration
# API key for service
MY_API_KEY=
```

Fill in values → restart app → values loaded.

**Priority**: Environment variables > `.env` file > defaults

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
├── __init__.py                  # Extension entry point (setup_*() functions)
├── config.py                    # Extension-specific settings (optional)
├── models/                      # Database models (prefix tables!)
├── schemas/                     # Pydantic schemas
├── services/                    # Business logic
├── tasks/                       # Celery background tasks
├── api/                         # API endpoints
│   └── router.py                # Route aggregator
└── admin/                       # Admin interface views
    └── views.py
```

**Note**: `.env.my_extension` goes in **project root**, not in extension folder.

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

### Creating Configuration
- Create `BaseSettings` class with `Field(description="...")` for all config vars
- Set `env_file=get_extension_env_path(__file__)` in `model_config`
- Call `generate_extension_env(__file__, YourSettingsClass)`
- Create singleton: `extension_settings = YourSettingsClass()`
- Edit auto-generated `.env.{extension_name}` file in project root

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
- Create `APIRouter()` in `api/feature.py` with route handlers and tags
- Inject services via type alias: `async def endpoint(service: MyServiceDep)`
- Aggregate routes in `api/router.py` using `router.include_router()`
- **Tags auto-discovered**: Define tags in router (e.g., `tags=["My Feature"]`), system automatically registers in API docs

### Creating Tasks
- Create task function with `@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.task_name")`
- Add `auto_import(__file__, "app.extensions.{name}.tasks")` to `tasks/__init__.py`

### Creating Admin Views
- Create `ModelView` subclass in `admin/views.py` with `model=YourModel`
- Set `name`, `icon`, `column_list` attributes for admin interface

---

## Testing

### Test Structure
- Create `app/extensions/{extension_name}/tests/bruno/` for Bruno API test collections
- Template available: `app/extensions/_example/tests/bruno/`
- See `docs/patterns/testing.md` for Bruno conventions

### PyTest Integration Tests
- Add `test_api.py`, `test_models.py`, `test_services.py`, `test_tasks.py` as needed
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

### Configuration Issues
- `.env.{extension_name}` in **project root**, not extension directory
- Empty values in `.env` → empty string (not defaults)
- Variable names are case-sensitive
- Check logs for "✓ Auto-generated .env.{extension_name}"

---

## Best Practices

1. **Table naming**: Always prefix with `{extension_name}_`
2. **Self-contained**: Extensions should not depend on each other
3. **Configuration**: Use extension-specific config.py for custom settings
4. **Environment files**: Keep `.env.{extension_name}` files in project root
5. **Test coverage**: Write tests for all extension features
6. **Documentation**: Document extension-specific behavior
7. **Migration discipline**: Always run migrations with same `ENABLED_EXTENSIONS` as deployment
