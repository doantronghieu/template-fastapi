# Schema and Model Patterns

Patterns for organizing schemas and models with consistency and clear separation of concerns.

---

## Schema Organization

### Location Strategy

| File | Purpose | Type System | Location |
|------|---------|-------------|----------|
| `api.py` | Request/response validation models | Pydantic | `{module}/schemas/` |
| `llm.py` | LLM structured output | Pydantic | `{module}/schemas/` |
| `dto.py` | Internal data transfer between layers | Pydantic | `{module}/schemas/` |
| `types.py` | External API type hints | TypedDict | `{module}/schemas/` |
| `{name}.py` | Shared schemas | Pydantic | `app/schemas/` |

**Module-level** (`{module}/schemas/`): Module-specific, co-located with code.

**Root-level** (`app/schemas/`): Shared models, cross-cutting concerns.

### Rationale

- Co-locate schemas with the code that uses them
- Reduce coupling between features
- Extract to root-level only when truly shared

---

## Type System Selection

### TypedDict (`types.py`)

Use for external API type hints when validation is unnecessary:

```python
from typing import Annotated, TypedDict

class WebhookPayload(TypedDict):
    event_type: Annotated[str, "Type of webhook event"]
    data: dict
```

**Benefits:** IDE autocomplete, type safety, zero runtime overhead.

### Pydantic (`api.py`, `llm.py`, `dto.py`)

Use for validation and serialization:

```python
from pydantic import BaseModel, Field

class CreateItemRequest(BaseModel):
    name: str = Field(description="Item name")
    quantity: int = Field(ge=1, description="Must be positive")
```

**Benefits:** Field constraints, OpenAPI docs, input validation.

**Summary:** `types.py` for external APIs; `api.py`/`llm.py`/`dto.py` for internal validation.

---

## Field Documentation

Replace functions/methods's docstring parameter descriptions (`Args` or `Returns`) with inline type annotations. Docstrings should describe only the function or class purpose—omit `Args` and `Returns` sections.

### TypedDict Fields

Use `Annotated` for field-level documentation:

```python
field_name: Annotated[str, "Description of the field"]
```

### Pydantic Fields

Use `Field(description=...)` for OpenAPI documentation:

```python
field_name: str = Field(alias="FieldName", description="Description of the field")
```

### Guidelines

- Document non-obvious fields; skip self-explanatory ones
- Keep descriptions concise but informative
- For Pydantic, combine descriptions with other `Field` parameters as needed

---

## Model Architecture

### SQLModel Base Pattern

Establish a single source of truth for field definitions using base classes.

**Domain model bases** (in `app/models/` or `{module}/models.py`):
- Base class with shared fields inheriting from `SQLModel`
- Table models inherit with `table=True`
- Response schemas can inherit for field reuse

**Schema-specific bases** (in `{module}/schemas/`):
- Co-locate with schemas for discoverability
- Used only by request/response schemas (API concerns)

### BaseTable for Common Metadata

Centralize common columns in a `BaseTable` class.

```python
class MyModel(MyModelBase, BaseTable, table=True):
    __tablename__ = "my_table"
```

Multiple inheritance order: `{Model}Base, BaseTable, table=True`

The domain base provides business fields, `BaseTable` provides metadata, and the concrete model defines table-specific configuration.

### Schema Composition via Multiple Inheritance

Compose schemas from multiple base classes for eliminating field redefinition:

- Combine different field groups through multiple inheritance
- Python's MRO applies left-to-right priority for conflicts
- Separate concerns: domain fields, API-specific fields, internal fields

---

## Field Customization

### Validators Over Redefinition

Add validation to inherited fields without duplicating definitions:

- `@field_validator("field_name")` for single-field validation
- `@model_validator(mode="after")` for cross-field validation
- Avoid redefining fields unless adding new constraints

### Field Override Guidelines

Override inherited fields only when adding database-specific configurations:

| Override | Don't Override |
|----------|----------------|
| Adding `index=True`, `unique=True` | Identical field definitions |
| Adding `sa_column=Column(...)` | Fields without new constraints |
| Configuring relationships | |

Include inline comments explaining overrides.

---

## Validation Strategy

### Validation Location Priority

1. **Pydantic `@field_validator`** — Single-field rules (preferred)
2. **Pydantic `@model_validator`** — Cross-field validation (requires POST with request body)
3. **API layer** — Only when Pydantic validation isn't feasible

### When to Validate at the API Layer

- GET endpoints using `Depends()` (cannot use `@model_validator`)
- Complex business logic requiring database queries
- Add inline comment explaining why

### POST for Complex Queries

Use POST with a request body instead of GET with query parameters when schema-level validation is required.

**Problem:** GET with `Depends()` instantiates schema with default `None` values before validation.

**Solution:** POST with request body ensures Pydantic validators run on complete payload.

---

## Avoid

- Creating schemas in API endpoint files
- Premature extraction to root-level
- Separate `bases.py` files unless genuinely shared
