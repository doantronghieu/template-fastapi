# Logging and Error Handling

This document describes logging strategies and error handling patterns.

## Logging Strategy

- Success operations: Log minimal essential information using f-string formatting
- Error conditions: Always include full stack traces using `exc_info=True` parameter for root cause analysis
- Embed contextual data directly in message strings rather than using logger's `extra` parameter (not visible in default formatters)

## Task ID Context Pattern

- Automatic task ID binding via Celery signals (`task_prerun`/`task_postrun`) in `app/core/celery.py`
- Task ID stored in `ContextVar` in `app/core/celery.py` (co-located with signals)
- Use `get_task_id()` helper in log messages: `logger.info(f"{get_task_id()}Processing...")`
- Task ID prefix format: `[b83caca6] ` (first 8 characters)
- No manual wrapping needed - signals automatically bind/unbind for every task
- Simple string interpolation approach avoids complex formatter/filter setup
- Benefits: Easy log correlation, debugging distributed task flows, production issue investigation

## Error Handling

- Re-raise exceptions after final retry attempt to expose full error context to calling code
- Avoid masking errors with user-friendly fallback messages that hide root causes during debugging
- Apply fail-open pattern for non-critical services to maintain availability when dependencies fail
