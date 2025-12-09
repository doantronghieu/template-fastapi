# Module Structure

Feature-based organization pattern for modular, scalable codebases.

## Core Principle

**Minimize coupling between slices, maximize coupling within a slice.**

Organize by feature, not by technical layer. Each feature folder contains everything needed for that capability—router, service, models, schemas, tests, etc. High cohesion within features, low coupling between unrelated features.

## Directory Structure

Hybrid approach: feature-based slices + root-level shared folders.

```
app/
├── core/                               # Cross-cutting infra (config.py, database.py, autodiscover.py, etc.)
├── features/                           # Vertical slices [default location for new code]
├── lib/                                # Provider-agnostic abstractions
├── integrations/                       # Provider-specific API clients
├── extensions/                         # Optional modules (opt-in)
├── models/                             # Shared database models
├── schemas/                            # Shared Pydantic schemas
├── services/                           # Cross-cutting business logic
├── tasks/                              # Core Celery tasks
├── templates/                          # Global Jinja2 templates
├── utils/                              # Pure utility functions
├── dependencies/                       # Shared FastAPI dependencies
└── main.py
```

## Module Template

All module types (`features/`, `lib/`, `integrations/`, `extensions/`) follow this template:

```
{module_name}/
├── __init__.py
├── router.py                   # API endpoints (auto-discovered)
├── webhooks.py                 # Webhook handlers (auto-discovered)
├── service.py                  # Business logic, orchestration
├── models.py                   # Database models (SQLModel)
├── tasks.py                    # Celery tasks (auto-discovered)
├── schedules.py                # Beat schedules (auto-discovered)
├── admin.py                    # SQLAdmin ModelView (auto-discovered)
├── schemas/
│   ├── api.py                  # Request/response (Pydantic)
│   ├── llm.py                  # LLM structured output (Pydantic)
│   ├── dto.py                  # Data transfer objects (Pydantic)
│   └── types.py                # External API type hints (TypedDict)
├── dependencies.py             # Dependency injection
├── constants.py                # Enums, error codes
├── exceptions.py               # Custom exceptions
├── config.py                   # Module-specific settings
├── utils.py                    # Helper functions
├── workflows/                  # Orchestration, state machines
├── resources/
│   ├── prompts/                # LLM prompt templates
│   └── templates/              # Jinja2 HTML templates
└── tests/
    ├── bruno/                  # API tests (Bruno .bru files)
    └── *.py                    # Unit tests (pytest)
```

## Module Type Differences

| Type | Discovery | Config | Typical Files | Purpose |
|------|-----------|--------|---------------|---------|
| `features/` | Auto | Always enabled | Full template | Core business logic |
| `lib/` | Auto | Always enabled | `base.py`, `factory.py`, `router.py` | Provider-agnostic abstractions |
| `integrations/` | Opt-out | `DISABLED_INTEGRATIONS=x,y` | `client.py`, `router.py`, `webhooks.py` | External API clients |
| `extensions/` | Opt-in | `ENABLED_EXTENSIONS=a,b` | Full template | Optional add-ons |

**lib/** additions:
- `base.py` - Protocol/ABC defining common interface
- `factory.py` - Factory function with `@lru_cache`

**integrations/** additions:
- `client.py` - SDK wrapper singleton (`@lru_cache`)

## Dependency Direction

```
app/main.py
    ↓
app/features/{feature}/router.py
    ↓
app/features/{feature}/service.py
    ↓
app/features/{feature}/models.py, schemas/
    ↓
app/models/, app/schemas/, app/services/
    ↓
app/lib/{capability}/
    ↓
app/integrations/{provider}/
    ↓
app/core/, app/utils/
```

**Rules:**
- Features never import from other features
- Services don't import from routers
- Cross-feature shared code → root-level folders (`app/models/`, `app/schemas/`, `app/lib/`)

## Handling Duplication

Small duplication between slices is acceptable. Extract to root-level only when:
- Logic is truly identical across features
- It's infrastructure/utility, not domain logic

**Extraction targets:**

| What | Where |
|------|-------|
| Models | `app/models/` |
| Schemas | `app/schemas/` |
| Pure utilities | `app/utils/` |
| Provider abstractions | `app/lib/` |
| Provider clients | `app/integrations/` |

## When to Nest Sub-Features

**Split indicators:**
- Service file exceeds 500 lines
- Multiple distinct workflows within feature
- Feature has clear sub-domains

## Anti-Patterns

| Avoid | Do Instead |
|-------|------------|
| Cross-feature imports | Extract to root-level (`app/models/`, `app/lib/`) |
| Business logic in router | Move to service |
| Tests far from code | Co-locate in feature `tests/` |
| Premature extraction | Keep in feature until 3+ users |
| All code at root-level | Start in `app/features/`, extract when shared |
