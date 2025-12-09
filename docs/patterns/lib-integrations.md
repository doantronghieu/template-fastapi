# Library Architecture Pattern

Implementation patterns for provider-agnostic abstractions via Strategy pattern.

## Two-Layer Architecture

| Layer | Location | Purpose |
|-------|----------|---------|
| Abstraction | `app/lib/{capability}/` | Protocol definitions, factory, dependencies |
| Implementation | `app/integrations/{provider}/` | Concrete provider implementations |

## Decision Criteria

**Create abstraction** (`app/lib/`) when:
- Multiple providers offer same functionality
- Runtime provider switching needed via config
- Business logic should be provider-agnostic

**Skip abstraction** (keep in `app/integrations/` only) when:
- Feature unique to one provider
- Tightly coupled to provider-specific patterns
- Abstraction would be premature

## Protocol vs ABC

| Pattern | Use When |
|---------|----------|
| `Protocol` | Pure interface, duck typing, no shared code |
| `ABC` | Shared utilities needed across implementations |

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Protocol/ABC | `{Capability}Provider` | `LLMProvider` |
| Implementation | `{Library}{Capability}Provider` | `LangChainLLMProvider` |
| Provider file | `{capability}.py` | `llm.py` |

## Factory Pattern

```python
# app/lib/{capability}/factory.py
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
    from app.lib.{capability}.base import {Capability}Provider

def get_{capability}_provider() -> "{Capability}Provider":
    from app.lib.{capability}.factory import get_{capability}_provider as factory
    return factory()

{Capability}ProviderDep = Annotated["{Capability}Provider", Depends(get_{capability}_provider)]
```

**Key points:**
- `TYPE_CHECKING` guard avoids circular imports
- Type alias (`{Capability}ProviderDep`) for clean endpoint signatures
- Enables testing/mocking via FastAPI's dependency override

## API Organization

| Location | Use Case |
|----------|----------|
| `app/lib/{capability}/router.py` | Provider-agnostic endpoints |
| `app/integrations/{provider}/router.py` | Provider-specific endpoints |

## Best Practices

1. **Protocol-based interfaces** - `lib/` defines contracts only
2. **Lazy imports in factory** - Avoids circular dependencies
3. **Configuration-driven** - Settings determine implementation at runtime
4. **Dependency injection** - FastAPI `Depends()` enables testing/mocking
5. **Integration isolation** - Each provider in own package with own config
