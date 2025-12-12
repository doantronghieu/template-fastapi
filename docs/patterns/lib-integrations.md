# Library Architecture Pattern

Implementation patterns for provider-agnostic abstractions via Strategy pattern.

## Two-Layer Architecture

| Layer | Purpose |
|-------|---------|
| `lib/{capability}/` | Protocol definitions, factory, dependencies |
| `integrations/{provider}/` | External API implementations (with secrets) |
| `lib/{capability}/providers/` | Pure Python implementations (no secrets) |

## Decision Criteria

**Create abstraction** (`app/lib/`) when:
- Multiple providers offer same functionality
- Runtime provider switching needed via config
- Business logic should be provider-agnostic

**Skip abstraction** (keep in `app/integrations/` only) when:
- Feature unique to one provider
- Tightly coupled to provider-specific patterns
- Abstraction would be premature

## lib/ vs integrations/ Decision

| Criteria | Use `integrations/` | Keep in `lib/` |
|----------|---------------------|----------------|
| API keys/secrets | ✅ | ❌ |
| External HTTP calls | ✅ | ❌ |
| Config in `.env` | ✅ | ❌ |
| Pure Python libs | ❌ | ✅ |
| Runs locally | ❌ | ✅ |

**Self-contained libs** (pure Python, no secrets) → `lib/{capability}/providers/`

**External API clients** (secrets required) → `integrations/{provider}/`

## Protocol vs ABC

| Pattern | Use When |
|---------|----------|
| `Protocol` | Pure interface, duck typing, no shared code |
| `ABC` | Shared utilities needed across implementations |

## Naming Conventions

| Component | Pattern |
|-----------|---------|
| Protocol/ABC | `{Operation}` or `{Operation}Provider` |
| Implementation | `{Provider}{Operation}` |
| Provider file | `{operation}.py` |

## Factory Pattern

```python
# app/lib/{capability}/factory.py
from functools import lru_cache

@lru_cache(maxsize=1)
def get_{operation}(provider: ProviderType) -> {Operation}:
    providers: dict[str, Callable[[], {Operation}]] = {
        ProviderType.{PROVIDER}.value: _get_{provider},
    }
    return providers[provider.value]()

def _get_{provider}() -> {Operation}:
    from app.integrations.{provider}.{operation} import {Provider}{Operation}
    return {Provider}{Operation}()
```

**Key points:**
- `@lru_cache` for singleton behavior
- Lazy imports in helper functions to avoid circular deps
- Config-driven provider selection

## Dependency Injection

```python
# app/lib/{capability}/dependencies.py
from typing import TYPE_CHECKING, Annotated
from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.{capability}.base import {Operation}

def get_{operation}_dependency() -> "{Operation}":
    from app.lib.{capability}.factory import get_{operation}
    return get_{operation}()

{Operation}Dep = Annotated["{Operation}", Depends(get_{operation}_dependency)]
```

**Key points:**
- `TYPE_CHECKING` guard avoids circular imports
- Type alias (`{Operation}Dep`) for clean endpoint signatures
- Enables testing/mocking via FastAPI's dependency override

## API Organization

| Location | Use Case |
|----------|----------|
| `app/lib/{capability}/router.py` | Provider-agnostic endpoints |
| `app/integrations/{provider}/router.py` | Provider-specific endpoints |

## When to Split Operations

**Split indicators:**
- Unrelated operations in same capability
- Adding operation would mix concerns
- Each operation needs own `{lib_core}` files

## Best Practices

1. **Protocol-based interfaces** - `lib/` defines contracts only
2. **Lazy imports in factory** - Avoids circular dependencies
3. **Configuration-driven** - Settings determine implementation at runtime
4. **Dependency injection** - FastAPI `Depends()` enables testing/mocking
5. **Integration isolation** - Each provider in own package with own config
6. **Self-contained libs in lib/** - No `integrations/` needed for pure Python packages
