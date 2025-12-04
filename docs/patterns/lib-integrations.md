# Library Architecture Pattern

Organization strategy for integrating third-party libraries with pluggable provider support via the Strategy pattern.

## Architecture Overview

**Two-layer structure:**

1. **Abstractions** (`app/lib/{capability}/`) - Protocol definitions, factory, dependencies
2. **Implementations** (`app/integrations/{library}/`) - Concrete provider implementations

**Directory structure:**
```
app/lib/{capability}/           # Abstraction layer
├── base.py                     # Protocol or ABC definition
├── config.py                   # Provider type enums
├── factory.py                  # Provider selection factory
├── dependencies.py             # FastAPI DI
├── schemas.py                  # Shared schemas (optional)
├── api.py                      # Provider-agnostic endpoints (optional)
└── cli.py                      # CLI tool (optional)

app/integrations/{library}/     # Implementation layer
├── __init__.py                 # setup_api(), setup_webhooks() hooks
├── {capability}.py             # Provider implementation (or provider.py)
├── config.py                   # Library-specific settings
├── client.py                   # SDK wrapper/singleton (optional)
├── schemas.py                  # Library-specific types (optional)
├── api.py                      # Library-specific endpoints (optional)
├── webhooks.py                 # Webhook handlers (optional)
├── dependencies.py             # Library-specific DI (optional)
└── services/                   # Complex business logic (optional)
```

## Decision Criteria

**Create abstraction** in `app/lib/{capability}/` when:
- Multiple providers offer same functionality
- Runtime provider switching needed via configuration
- Interface relatively standardized across providers
- Business logic should be provider-agnostic

**Skip abstraction** (keep in `app/integrations/{library}/` only) when:
- Feature unique to one library with no equivalent elsewhere
- Tightly coupled to library-specific patterns
- Abstraction would be premature or forced

## Protocol vs ABC

| Pattern | Use When |
|---------|----------|
| `Protocol` | Pure interface, duck typing, no shared code |
| `ABC` | Shared utilities needed across implementations |

## Provider Implementation Pattern

**Naming conventions:**
- Protocol/ABC: `{Capability}Provider`
- Implementation: `{Library}{Capability}Provider`
- Provider file: `{capability}.py` or `provider.py`

**Factory with lazy imports:**
```python
# app/lib/{capability}/factory.py
from collections.abc import Callable
from functools import lru_cache

@lru_cache(maxsize=1)
def get_{capability}_provider() -> {Capability}Provider:
    providers: dict[str, Callable[[], {Capability}Provider]] = {
        ProviderType.LIBRARY.value: _get_{library}_provider,
    }
    # ... factory logic with lazy import

def _get_{library}_provider() -> {Capability}Provider:
    from app.integrations.{library}.{capability} import {Library}{Capability}Provider
    return {Library}{Capability}Provider()
```

**Dependency injection:**
- Pattern: provider function returns instance, type alias for injection
- Use `TYPE_CHECKING` guard to avoid circular imports
- Inject in endpoints via type alias parameter

```python
# app/lib/{capability}/dependencies.py
from typing import TYPE_CHECKING, Annotated
from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.{capability}.base import {Capability}Provider

def get_{capability}_provider() -> "{Capability}Provider":
    from app.lib.{capability}.factory import get_{capability}_provider as factory
    return factory()

{Capability}ProviderDep = Annotated["{Capability}Provider", Depends(get_{capability}_provider)]
```

## API Organization

**Two locations for `api.py`:**

| Location | Use When | Route Pattern |
|----------|----------|---------------|
| `app/lib/{capability}/api.py` | Provider-agnostic endpoints | `/api/lib/{capability}/{endpoint}` |
| `app/integrations/{library}/api.py` | Library-specific endpoints | `/api/integrations/{library}/{endpoint}` |

**Auto-discovery:**
- `app/api/lib/__init__.py` scans `app/lib/*/api.py`
- `app/integrations/` uses `setup_api()` hook in `__init__.py`

## Best Practices

1. **Protocol-based interfaces** - `lib/` defines contracts only
2. **Lazy imports in factory** - Avoids circular dependencies
3. **Configuration-driven** - Settings determine implementation at runtime
4. **Dependency injection** - FastAPI `Depends()` enables testing/mocking
5. **Integration isolation** - Each provider in own package with own config
6. **Flat structure** - Avoid deep nesting

## Relationship with Features

```
app/lib/{capability}/           # Interfaces + factories
app/integrations/{library}/     # Implementations
app/features/{domain}/          # Business logic using lib/ interfaces
```

Features consume lib/ interfaces via dependency injection, remaining provider-agnostic.
