# Extension Domain Pattern

Vertical slice organization for shared integrations within extensions.

## Core Principle

**Features consume domains, domains wrap integrations.**

## Structure

```
app/extensions/{ext}/
├── core/                       # Cross-cutting infra
├── domains/                    # Shared integration wrappers
│   └── {domain}/
│       ├── __init__.py         # Re-export
│       ├── schemas/
│       └── service.py          # Integration wrapper
├── features/                   # Auto-discovered business features
│   └── {feature}/
│       ├── router.py, service.py, models.py, schemas/
└── __init__.py
```

## When to Use

| Scenario | Solution |
|----------|----------|
| Single feature | Keep in `features/` only |
| Multiple features share integration | Extract to `domains/` |
| Extension-specific config for integration | `domains/{name}/config.py` |

## domains/ vs features/

| Aspect | `domains/` | `features/` |
|--------|-----------|-------------|
| Purpose | Shared wrappers | Business features |
| Discovery | Manual import | Auto-discovered |
| Contains | schemas/, service.py | Full module template |

## Dependency Direction

```
features/ → domains/ → app/integrations/ → app/lib/
```

- Features import domains, never reverse
- Domains import root integrations, never features
- No cross-domain imports

## Service Pattern

```python
# domains/{domain}/service.py
class {Domain}Service:
    def __init__(self, client):
        self.client = client

    def {operation}(self, **kwargs) -> {Schema}:
        return {Schema}(**self.client.{method}(**kwargs))

def create_{domain}_service(client) -> {Domain}Service:
    return {Domain}Service(client)
```

```python
# domains/{domain}/__init__.py
from .schemas.{schema_type} import {Schema1}, {Schema2}
from .service import {Domain}Service, create_{domain}_service
__all__ = ["{Schema1}", "{Schema2}", "{Domain}Service", "create_{domain}_service"]
```

## Anti-Patterns

| Avoid | Do Instead |
|-------|------------|
| Domain with only schemas | Keep in feature |
| Domain importing feature | Invert dependency |
| Cross-domain imports | Extract to `core/` |
| Duplicating integration logic | Wrap, don't copy |
