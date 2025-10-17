# Library Architecture Pattern

Organization strategy for integrating third-party libraries with pluggable provider support via the Strategy pattern.

## Universal vs Library-Specific Architecture

**Decision criteria for abstraction layers:**

Create abstraction in `app/lib/{capability}/` when:
- Multiple providers offer same functionality (LLM, embeddings, etc.)
- Runtime provider switching needed via configuration
- Interface relatively standardized across providers
- Business logic should be provider-agnostic

Keep in library directory `app/lib/{library}/` when:
- Feature unique to one library (chains, agents, retrievers, etc.)
- No equivalent functionality in other providers
- Tightly coupled to library-specific patterns
- Abstraction would be premature or forced

**Directory structure:**
```
app/lib/
├── {capability}/             # Abstraction: base.py (Protocol), config.py (enums),
│                             # factory.py (selection), dependencies.py (DI)
└── {library}/                # Implementation: {capability}.py (provider class),
                              # {feature}.py (library-specific), dependencies.py
```

Avoid deep nesting (`app/lib/ai/llm/`) - use flat structure with clear capability names.

## Provider Implementation Pattern

**Interface and naming:**
- Define interface using `Protocol` or `ABC` in `base.py`
- Name providers specifically: `{Library}{Capability}Provider` (e.g., `LangChainLLMProvider`)
- Each library implements protocol in its own directory
- Avoids generic names, enables multiple capabilities per library

**Factory with type-safe configuration:**
- Create provider type enum in config (e.g., `LLMProviderType`)
- Factory maps enum values to provider classes for runtime selection
- Settings import enum and use `.value` for defaults
- Ensures consistency, prevents typos, validates at startup

**Dependency injection:**
- Co-locate: library deps in `app/lib/{library}/dependencies.py`, core deps in `app/core/dependencies.py`
- Pattern: provider function returns instance, type alias for injection via `Annotated[Type, Depends(fn)]`
- Use `TYPE_CHECKING` guard to avoid circular imports
- Inject in endpoints via type alias parameter for clean signatures

## Test Schema Organization

**Separation strategy:**
- Domain/business schemas: `app/schemas/` for production endpoints
- Library test schemas: `app/api/lib/schemas/{capability}.py` for testing
- Use directory (not single file) organized by capability
- Share schemas across related test endpoints to avoid duplication
