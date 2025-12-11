# Prompt & Schema Design Patterns

Guidelines for designing LLM prompts and Pydantic schemas that work cohesively.

## Core Principle

**Prompts orchestrate; schemas define structure.**

- Schema fields contain all content-related metadata (descriptions, constraints, types)
- Prompts focus on workflow orchestration, not field-level details
- Avoid duplication between prompt text and schema definitions

## Schema Design Patterns

### 1. Modular Chain-of-Thought

Include reasoning within data models to capture localized rationale alongside structured output. This enables the LLM to explain decisions per item.

### 2. Enumeration with Fallback

Always include an `OTHER` or fallback option in enums to handle edge cases gracefully. Prevents forced misclassification.

### 3. Dynamic Key-Value Properties

Use key-value pair models for arbitrary or evolving data types. Provides flexibility without schema changes.

## JSON Schema Visibility

Understanding what the LLM receives:

| Python Construct          | In Schema |
|---------------------------|-----------|
| `# inline comment`        | ❌ No     |
| `Enum` class docstring    | ✅ Yes    |
| `Field(description=...)`  | ✅ Yes    |
| `BaseModel` class docstring | ✅ Yes  |

## Best Practices

- Use `Field(description=...)` for all fields—this is the primary way to guide LLM output
- Keep docstrings single-line for enum classes (multiline can cause issues with some providers)
- Format BaseModel docstrings appropriately for readability in generated schemas
- Migrate field-specific guidance from prompts into schema definitions
