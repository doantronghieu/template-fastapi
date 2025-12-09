# Auto-Discovery System

Convention-based module discovery. Drop files with correct names → auto-registered. No core code changes.

## Module Types

| Type | Discovery | Config | Router URL | Webhooks URL |
|------|-----------|--------|------------|--------------|
| `features/` | Auto | Always enabled | `/api/features/{name}/*` | `/api/webhooks/{name}/*` |
| `lib/` | Auto | Always enabled | `/api/lib/{name}/*` | — |
| `integrations/` | Opt-out | `DISABLED_INTEGRATIONS=x,y` | `/api/integrations/{name}/*` | `/api/webhooks/{name}/*` |
| `extensions/` | Opt-in | `ENABLED_EXTENSIONS=a,b` | `/api/extensions/{name}/*` | `/api/webhooks/{name}/*` |

## File Conventions

| File | Registers To | Required Export |
|------|--------------|-----------------|
| `router.py` | Router URL (see above) | `router: APIRouter` |
| `webhooks.py` | Webhooks URL (see above) | `router: APIRouter` |
| `models.py` | Alembic migrations | SQLModel classes |
| `tasks.py` | Celery worker | `@celery_app.task` functions |
| `schedules.py` | Celery beat | `SCHEDULES: dict` |
| `admin.py` | SQLAdmin `/admin` | `ModelView` subclasses |

**Discovery rules:**
- Directory must have `__init__.py`
- Import errors logged, not fatal

## Quick Start

```bash
# Feature (auto-enabled)
mkdir -p app/features/{feature_name} && touch app/features/{feature_name}/{__init__,router,service,models}.py

# Integration (opt-out)
mkdir -p app/integrations/{provider_name} && touch app/integrations/{provider_name}/{__init__,router,webhooks,client}.py

# Extension (opt-in, add to ENABLED_EXTENSIONS)
mkdir -p app/extensions/{extension_name} && touch app/extensions/{extension_name}/{__init__,router,tasks,schedules}.py

# Lib (auto-enabled)
mkdir -p app/lib/{capability_name} && touch app/lib/{capability_name}/{__init__,base,factory,router}.py
```

## Component Templates

**router.py**
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_{resources}():
    return []
```

**webhooks.py**
```python
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/{webhook_path}")
async def handle_{webhook_name}(request: Request):
    return {"received": True}
```

**models.py**
```python
from sqlmodel import SQLModel, Field

class {ModelName}(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

**tasks.py**
```python
from app.core.celery import celery_app
from app.core.config import settings

@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.{task_name}")
def {task_name}({task_args}):
    pass
```

**schedules.py**
```python
from celery.schedules import crontab
from app.core.config import settings

SCHEDULES = {
    "{schedule_name}": {
        "task": f"{settings.CELERY_TASKS_MODULE}.{task_name}",
        "schedule": crontab(minute="*/5"),
        "args": (),
    },
}
```

**admin.py**
```python
from sqladmin import ModelView
from .models import {ModelName}

class {ModelName}Admin(ModelView, model={ModelName}):
    column_list = [{ModelName}.id]
```
