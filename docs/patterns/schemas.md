# Schema and Model Patterns

This guide establishes patterns for organizing schemas and models, ensuring consistency, reusability, and clear separation of concerns.

---

## Schema Organization

### Location

All request and response schemas belong in `app/schemas/{module}.py`. Use a flat structure—avoid nested directories like `app/schemas/{category}/{module}.py`.

Define schemas in `app/schemas/` first, then import them into API endpoints. API files should focus purely on HTTP handling—never define schemas inline.

### Rationale

- Schemas become immediately reusable across API modules, services, and background tasks
- Clear separation of concerns: the API layer handles requests/responses; schemas handle validation
- Eliminates refactoring costs when reuse is needed later

---

## Type System Selection

### TypedDict

Use TypedDict for external API type hints (webhooks, SDK responses) when validation is unnecessary. Place these in `types.py` within integration or library directories.

TypedDict provides IDE autocomplete and type safety with zero runtime overhead. External APIs validate their own payloads—we don't need to re-validate them.

### Pydantic

Use Pydantic for request/response validation on FastAPI endpoints. Place these in `app/schemas/`.

Pydantic enforces field constraints and generates OpenAPI documentation automatically. Use it to validate untrusted user input to our endpoints.

**Summary**: Clients use TypedDict for external API calls; endpoints use Pydantic for request validation.

---

## Field Documentation

Replace docstring parameter descriptions with inline type annotations. Docstrings should describe only the function or class purpose—omit `Args` and `Returns` sections.

**Targets**: All methods and functions that currently have `Args` or `Returns` in their docstrings.

### TypedDict Fields

Use `Annotated` for field-level documentation:

```python
field_name: Annotated[str, "Description of the field"]
```

### Pydantic Fields

Use `Field(description=...)` for documentation that appears in OpenAPI/Swagger:

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

Establish a single source of truth for field definitions using base classes with `Field` descriptions.

**Domain model bases** define core business fields:
- Create a base class inheriting from `SQLModel` with shared fields
- Locate in `app/models/` alongside table models
- Table models inherit from the base with `table=True`
- Response schemas inherit from the same base for field reuse

**Schema-specific bases** define API concerns:
- Co-locate with schemas in `app/schemas/` for discoverability
- Used only by request/response schemas, never by table models
- Group related optional parameters (e.g., external channel fields, internal UUID fields)

### BaseTable for Common Metadata

Centralize common columns in a `BaseTable` class to eliminate repetition.

Use multiple inheritance with this order: `{Model}Base, BaseTable, table=True`. The domain base provides business fields, `BaseTable` provides metadata, and the concrete model defines table-specific configuration.

```python
class MyModel(MyModelBase, BaseTable, table=True):
    __tablename__ = "my_table"
```

### Schema Composition via Multiple Inheritance

Compose schemas from multiple base classes (similar to Zod's `.merge()` or TypeScript intersection types):

- Combine different field groups through multiple inheritance
- Python's MRO applies left-to-right priority for conflicts
- Separate concerns: domain fields, API-specific fields, internal fields, authentication fields
- Request schemas combine necessary bases without field redefinition

---

## Field Customization

### Validators Over Redefinition

Add validation to inherited fields without duplicating definitions (similar to Zod's `.refine()`):

- Use `@field_validator("field_name")` for single-field validation
- Use `@model_validator(mode="after")` for cross-field validation
- Avoid redefining fields unless adding new constraints
- Validators receive values, perform checks, and raise `ValueError` or return processed values

### Field Override Guidelines

Override inherited fields only when adding database-specific configurations:

| Override | Don't Override |
|----------|----------------|
| Adding `index=True`, `unique=True` | Identical field definitions |
| Adding `sa_column=Column(...)` | Fields without new constraints |
| Configuring relationships | |

When overriding, always include an inline comment explaining why (e.g., `# Override to add unique constraint`). Note that field descriptions may be lost when overriding due to SQLModel limitations.

---

## Validation Strategy

### Validation Location Priority

1. **Pydantic `@field_validator`** — Single-field rules (preferred)
2. **Pydantic `@model_validator`** — Cross-field validation (requires POST with request body)
3. **API layer** — Only when Pydantic validation isn't feasible

### When to Validate at the API Layer

- GET endpoints using `Depends()` (cannot use `@model_validator`)
- Complex business logic requiring database queries or external service calls
- Always add an inline comment explaining why validation is at the API layer

### POST for Complex Queries

Use POST with a request body instead of GET with query parameters when schema-level validation is required.

**Problem**: GET with `Depends()` instantiates the schema with default `None` values before validation runs.

**Solution**: POST with a request body (no `Depends()`) ensures Pydantic validators run on the complete payload, enabling `@model_validator` for cross-field checks.

This pattern is common for complex query endpoints requiring "at least one of" validation logic. Document this choice in the endpoint docstring when applicable.

---

## File Organization

### Co-location Strategy

**Domain bases** → Keep in same file as table models (`app/models/`)
- Used by table models and response schemas

**Schema bases** → Keep in same file as request/response schemas (`app/schemas/`)
- Used only by API schemas, improving discoverability

### Avoid

Creating separate `bases.py` files unless bases are genuinely shared across many unrelated modules.