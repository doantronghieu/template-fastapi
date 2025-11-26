# Schema and Model Patterns

This document describes patterns for organizing and implementing schemas and models.

## Schema Location and Organization

**Principle**: Schemas belong in `app/schemas/` from the start for reusability and separation of concerns.

**Location Rules**:
- **Request/Response schemas**: Always in `app/schemas/{module}.py` (e.g., `app/schemas/messenger.py`)
- **Flat structure**: Use `app/schemas/messenger.py`, not nested `app/schemas/integration/messenger.py`
- **API endpoints**: Import schemas, focus purely on HTTP handling

**Reasoning**:
- Schemas become immediately reusable across API modules, services, and background tasks
- Clear separation: API layer handles requests/responses, schemas handle validation
- Consistency with project pattern where `app/schemas/` is single source of truth
- Avoids refactoring cost of extracting schemas later when reuse is needed

**Pattern**: Define schemas in `app/schemas/` first, then import into API endpoints - never define schemas inline in API files.

## TypedDict vs Pydantic Schemas

**Principle**: Use TypedDict for external API type hints without validation, Pydantic for internal API validation.

**TypedDict** (`types.py` in integration/library dirs): Runtime type hints for external API structures (webhooks, SDK responses) without validation overhead. Provides IDE autocomplete and type safety at zero cost.

**Pydantic** (`app/schemas/`): Request/response validation for our FastAPI endpoints with field constraints and automatic OpenAPI documentation. External APIs validate their own payloads - we validate untrusted user input to our endpoints.

**Pattern**: Clients use TypedDict for external API calls, endpoints use Pydantic for request validation.

## Type Hints & Field Documentation

**Principle**: Replace docstring parameter descriptions with inline type annotations. Docstrings describe only function/class purpose—no param/return lists.

**TypedDict fields**: Use `Annotated[Type, "description"]` for field-level documentation. Provides context without runtime overhead.

```python
Id: Annotated[str, "Record ID"]
```

**Pydantic fields**: Use `Field(description="...")` for field documentation. Descriptions appear in OpenAPI/Swagger docs automatically.

```python
id: str = Field(alias="Id", description="Record ID")
```

**Guidelines**:
- Document non-obvious fields
- Skip documentation for self-explanatory fields 
- Keep descriptions concise but still informative
- For Pydantic, combine with other Field parameters

## SQLModel Base Pattern ("Fat Models")

**Principle**: Single source of truth for field definitions with descriptions in base classes.

- **Domain model bases** define core business fields with Field descriptions
  - Create base class inheriting from `SQLModel` with shared fields
  - Located in `app/models/` alongside table models
  - Table model inherits from base with `table=True` parameter
  - Response schemas inherit from same base for field reuse
- **Schema-specific bases** define API/request-specific concerns
  - Co-located with schemas in same file for discoverability
  - Used only by request/response schemas, never by table models
  - Group related optional parameters (e.g., external channel fields, internal UUID fields)

## BaseTable Pattern for Common Metadata

**Principle**: Centralize common columns/metadata in `BaseTable` to eliminate repetition.

**Pattern**: Use multiple inheritance with order `DomainBase, BaseTable, table=True`. Domain base provides business fields, BaseTable provides common metadata, concrete model defines table-specific configuration. Example: `class Entity(EntityBase, BaseTable, table=True)`

## Multiple Inheritance for Schema Composition

**Principle**: Compose schemas from multiple base classes (similar to Zod's `.merge()` or TypeScript intersection types).

- Inherit from multiple base classes to combine different field groups
- Python MRO (Method Resolution Order) applies left-to-right priority for conflicts
- Enables maximum reusability through composition
- Separate concerns: domain fields, API-specific fields, internal fields, authentication fields
- Request schemas combine all necessary bases without field redefinition

## Field Validators Over Redefinition

**Principle**: Add validation without duplicating field definitions using Pydantic decorators.

- Use `@field_validator("field_name")` decorator to add validation to inherited fields
- Use `@model_validator(mode="after")` for cross-field validation logic
- Avoid redefining fields in child schemas unless adding new constraints
- Similar to Zod's `.refine()` method - extend behavior without duplication
- Validator method receives value, performs checks, raises ValueError or returns processed value

## Field Override Guidelines

**Principle**: Only override inherited fields when adding database-specific configurations.

- **Override when needed**: Adding `index=True`, `unique=True`, `sa_column=Column(...)`, etc. or relationship configs
- **Don't override unnecessarily**: If field definition is identical to parent, don't redefine
- **Always add inline comment**: Explain why override is needed (e.g., "# Override to add unique constraint")
- **Accept trade-off**: Field descriptions may be lost when overriding (SQLModel limitation)

## POST Method for Complex Queries

**Principle**: Use POST with request body (instead of GET with query params) to enable schema-level validation.

- **Problem**: GET with `Depends()` instantiates schema with default None values before validation
- **Solution**: Use POST method with request body parameter (no `Depends()`)
- **Benefit**: Pydantic validators run on complete payload, enabling `@model_validator` cross-field checks
- **Documentation**: Add note in endpoint docstring explaining POST usage for validation
- **Pattern**: Common for complex query endpoints requiring "at least one of" logic

## Schema Validation Best Practices

**Validation Location Priority**:
1. **Pydantic `@field_validator`** - Single-field validation rules (preferred)
2. **Pydantic `@model_validator`** - Cross-field validation (requires POST request body)
3. **API layer** - Only when Pydantic validation isn't feasible

**When validation must stay at API layer**:
- GET endpoints with query parameters using `Depends()` (can't use `@model_validator`)
- Complex business logic requiring database queries or external service calls
- Always add inline comment explaining why validation is at API layer

## Base Class Organization

**Co-location Strategy**:
- **Domain bases with models**: Keep base classes in same file as table models (`app/models/`)
  - Reason: Domain-specific, used by table models and response schemas
  - Example: Entity base next to entity table definition
- **Schema bases with schemas**: Keep API-specific bases in same file as request/response schemas (`app/schemas/`)
  - Reason: Only used by API schemas, not domain models
  - Example: Query parameter bases, external integration bases
  - Improves discoverability when working on API layer

**Avoid**: Creating separate `bases.py` files unless bases are truly shared across many unrelated modules.
