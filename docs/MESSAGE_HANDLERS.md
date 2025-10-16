# Custom Channel Message Handlers

Enable extensions to provide custom AI responses for messaging channels (Messenger, WhatsApp, Telegram) without modifying core code.

## Overview

**Purpose**: Allow extensions to override default AI behavior with domain-specific logic, custom prompts, and external integrations.

**Key Principle**: Convention over configuration - enable an extension, its handler automatically processes all channel messages.

**Architecture**:
- **Protocol-based**: Extensions implement `ChannelMessageHandler` protocol with single `handle_message()` method
- **Registry pattern**: Handlers auto-register via `setup_message_handlers()` hook at startup
- **Automatic selection**: First enabled extension's handler used; falls back to default LLMService if none
- **Zero coupling**: Core webhook code never references specific extensions

## Core Concepts

### Handler Selection Flow

1. App/worker starts → loads extension handlers → stores in registry
2. Message arrives → registry returns first registered handler or default
3. Handler processes message → saves user message, generates AI response, saves AI response
4. Response sent via channel API

### Handler Responsibilities

Implement `handle_message()` to:
- Save incoming user message to database
- Generate AI response using custom logic (LLM service, rules, external APIs)
- Save AI response to database
- Return response text for sending

## Implementation

### Step 1: Create Handler Class

Create file at `app/extensions/{extension_name}/handlers/channel_message.py`:

```python
class MyExtensionChannelMessageHandler:
    async def handle_message(
        self, sender_id: str, message_content: str,
        channel_type: ChannelType, channel_conversation_id: str,
        session: AsyncSession
    ) -> str:
        # 1. Save user message via MessagingService
        # 2. Generate AI response (custom logic here)
        # 3. Save AI response via MessagingService
        # 4. Return response text
```

**Customization points**:
- Inject extension-specific services and data sources
- Use custom LLM prompts with domain context
- Apply business rules before/after AI generation
- Integrate external APIs for data enrichment

### Step 2: Register Handler

Add to extension's `__init__.py`:

```python
def setup_message_handlers() -> None:
    from pathlib import Path
    from app.services.handlers import channel_message_handler_registry
    from .handlers.channel_message import MyExtensionChannelMessageHandler

    extension_name = Path(__file__).parent.name
    handler = MyExtensionChannelMessageHandler()
    channel_message_handler_registry.register(extension_name, handler)
```

### Step 3: Enable Extension

Set in `.env`:
```bash
ENABLED_EXTENSIONS=my_extension
```

Handler automatically loads and processes all channel messages.

## Configuration

### Single Extension (Recommended)

Enable one extension with messaging capability - its handler processes all messages.

### Multiple Extensions

If multiple extensions register handlers:
- First enabled extension's handler wins
- Warning logged about multiple handlers
- Control priority via `ENABLED_EXTENSIONS` order: `extension_a,extension_b` (extension_a wins)

### Disabling

Remove extension from `ENABLED_EXTENSIONS` - automatically falls back to default LLMService.

## Advanced Patterns

### Hybrid Handler

Combine extension logic with default LLM:

**Strategy**: Check message content/context, use custom logic for domain queries, delegate general conversation to default LLM.

**Implementation**: Import `LLMService` and `get_llm_provider()`, instantiate within handler, conditionally invoke based on message analysis.

### Service Injection

Inject extension services into handler via constructor for access to domain-specific data sources and business logic.

### Context-Aware Responses

Query conversation history, user attributes, or external systems within `handle_message()` to tailor responses.

### Custom Prompts

Build domain-specific prompt templates with conversation context, user data, and business rules before LLM invocation.

## Use Cases

Extensions can customize AI responses for domain-specific workflows and data integrations. Common patterns include data retrieval from external systems, workflow automation based on message content, context-enriched prompts with user/business data, and conditional logic for routing or escalation.

## Testing

### Manual Testing

1. Start services: `make dev` (FastAPI) and `make infra-up` (Celery)
2. Send test message to channel webhook
3. Check logs for handler selection confirmation

**Expected log**: `INFO: Using extension channel message handler: MyExtensionChannelMessageHandler (extension: my_extension)`

### Unit Testing

Test handlers in isolation with mock database sessions and sample messages. Verify handler saves messages correctly and returns expected AI responses.

### Integration Testing

Test complete flow with actual channel webhooks and message sending to verify end-to-end functionality.

## Troubleshooting

### Handler Not Used

**Check**: Extension enabled in `.env`, handler registered (check startup logs), no import errors during registration

**Solution**: Review logs for registration messages, verify extension name matches between `.env` and registration code

### Default Handler Always Used

**Check**: `setup_message_handlers()` hook exists in extension's `__init__.py`, handler registration called, extension listed in `ENABLED_EXTENSIONS`

**Solution**: Add debug logging to `setup_message_handlers()`, verify hook executes at startup

### Multiple Handlers Warning

**Cause**: Multiple extensions registered handlers

**Solutions**: Enable single extension with messaging, reorder `ENABLED_EXTENSIONS` to prioritize, or remove handler from non-primary extension

### Import Errors

**Cause**: Missing dependencies or incorrect import paths

**Solution**: Wrap handler registration in try-except, check handler file location matches import path, verify all dependencies installed

## Best Practices

**Single Responsibility**: One handler per extension, focused on single domain
**Clear Naming**: Use descriptive class names indicating purpose (e.g., `{Domain}ChannelMessageHandler`)
**Graceful Degradation**: Consider hybrid approach with fallback to default LLM for out-of-domain queries
**Logging**: Log handler decisions and AI generation steps for debugging
**Testing**: Unit test with various message types and edge cases
**Documentation**: Document what messages/scenarios handler processes

## Migration from can_handle() Pattern

Previous implementation required `can_handle()` method to determine ownership per message.

**New approach**: Handler automatically used when extension enabled - simpler, no per-message checks needed.

**Migration**: Remove `can_handle()` method, keep only `handle_message()`. Selection now happens at startup, not per message.

## File Reference

**Core**:
- Registry & Protocol: `app/services/handlers/channel_message_registry.py`
- Default Handler: `app/services/handlers/channel_message_default.py`
- Package Exports: `app/services/handlers/__init__.py`
- Task Integration: `app/tasks/channel_tasks.py`
- Startup Loading: `app/main.py` (lifespan) and `app/core/celery.py`

**Extension Example**:
- Handler: `app/extensions/hotel/handlers/channel_message.py`
- Registration: `app/extensions/hotel/__init__.py` (setup_message_handlers)
- Template: `app/extensions/_example/__init__.py`

## Quick Reference

**Create handler**: `handlers/channel_message.py` with `handle_message()` method
**Register**: Import registry, call `register("extension_name", handler)`
**Enable**: Add to `ENABLED_EXTENSIONS` in `.env`
**Verify**: Check startup logs for registration confirmation
**Test**: Send message, verify handler selection in logs
