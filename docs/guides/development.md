# Development Guide

Step-by-step workflows for common development tasks.

---

## Adding a Feature

1. Create feature directory:
   ```bash
   mkdir -p app/features/{name} && touch app/features/{name}/{__init__,router,service,models}.py
   ```

2. Add router (`router.py`):
   ```python
   from fastapi import APIRouter

   router = APIRouter()

   @router.get("/")
   async def list_{entities}():
       return []
   ```

3. Add service (`service.py`) with business logic

4. Add models (`models.py`) if needed, then generate migration:
   ```bash
   make db-migrate message="add {table}" && make db-upgrade
   ```

Router auto-registers to `/api/features/{name}/*`.

---

## Adding an Endpoint

**Within existing module:**
1. Add route to `{module}/router.py`
2. Inject dependencies via type alias: `async def endpoint(service: ServiceDep)`

**For webhooks:**
1. Create `{module}/webhooks.py` with `router = APIRouter()`
2. Auto-registers to `/api/webhooks/{module_name}/*`

---

## Adding a Background Task

1. Create `{module}/tasks.py`:
   ```python
   from app.core.celery import celery_app
   from app.core.config import settings

   @celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.{task_name}")
   def process_{entity}({entity}_id: int):
       pass
   ```

2. Trigger: `process_{entity}.delay({entity}_id)` or `.apply_async()`

---

## Adding a Beat Schedule

1. Create `{module}/schedules.py`:
   ```python
   from celery.schedules import crontab
   from app.core.config import settings

   SCHEDULES = {
       "{task_name}": {
           "task": f"{settings.CELERY_TASKS_MODULE}.{task_name}",
           "schedule": crontab(hour=0, minute=0),
           "args": (),
       },
   }
   ```

2. Schedule keys auto-prefixed with module name

---

## Adding an Admin View

1. Create `{module}/admin.py`:
   ```python
   from sqladmin import ModelView
   from .models import {Entity}

   class {Entity}Admin(ModelView, model={Entity}):
       column_list = [{Entity}.id, {Entity}.name, {Entity}.created_at]
       column_searchable_list = [{Entity}.name]
   ```

2. View auto-registers to `/admin`

---

## Adding a Service

1. Create `{module}/service.py`:
   ```python
   class {Entity}Service:
       async def create(self, data: Create{Entity}Request) -> {Entity}:
           ...
   ```

2. Add dependency in `{module}/dependencies.py`:
   ```python
   from typing import Annotated
   from fastapi import Depends

   def get_{entity}_service() -> {Entity}Service:
       return {Entity}Service()

   {Entity}ServiceDep = Annotated[{Entity}Service, Depends(get_{entity}_service)]
   ```

---

## Adding a Library Abstraction

For provider-agnostic capabilities:

1. Create abstraction in `app/lib/{capability}/`:
   - `base.py` - Protocol/ABC interface
   - `factory.py` - Provider factory with `@lru_cache`
   - `dependencies.py` - FastAPI dependency

2. Implement provider in `app/integrations/{provider}/{capability}.py`

3. Register in factory, configure in settings

---

## Adding an Integration

For external API clients:

1. Create integration directory:
   ```bash
   mkdir -p app/integrations/{provider} && touch app/integrations/{provider}/{__init__,client,router,webhooks}.py
   ```

2. Add client (`client.py`) with async methods and `@lru_cache` singleton

3. Add webhook handlers (`webhooks.py`) for incoming events

4. Disable via `DISABLED_INTEGRATIONS={provider}` if needed

---

## Shared vs Module-Level

| Criterion | Module-Level | Root-Level |
|-----------|--------------|------------|
| Used by | 1-2 features | 3+ features |
| Location | `app/{module_type}/{name}/` | `app/{models,schemas,services}/` |
| Guideline | Start here | Extract when shared |

---

## Code Style

**Type hints:** Use `Annotated[Type, "description"]` for parameters needing explanation.

**Docstrings:** Describe function purpose only—omit `Args` and `Returns` sections.

**Package exports:** Use `__all__ = ["Class"]` for explicit exports.

---
