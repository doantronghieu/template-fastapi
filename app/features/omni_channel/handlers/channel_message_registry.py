"""Channel message handler protocol and registry for extensible AI response generation.

Enables extensions to provide custom message handling logic for messaging channels
(Messenger, WhatsApp, Telegram, etc.) without modifying core code.

Architecture:
- Protocol-based handler interface for extensions to implement
- Registry pattern for handler registration via extension hooks
- Automatic handler selection: enabled extension's handler used if available
- Convention over configuration: no need for can_handle() checks
"""

import logging
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ChannelType

logger = logging.getLogger(__name__)


class ChannelMessageHandler(Protocol):
    """Protocol for channel message handlers.

    Extensions implement this protocol to provide custom AI response logic for
    messaging channels (Messenger, WhatsApp, Telegram, etc.).
    When extension is enabled, its handler automatically processes all channel messages.
    """

    async def handle_message(
        self,
        sender_id: str,  # Channel-specific user identifier
        message_content: str,
        channel_type: ChannelType,
        channel_conversation_id: str,
        session: AsyncSession,
    ) -> str:
        """Process message and generate AI response.

        Note:
            Handler is responsible for complete processing flow:
            - Save user message to database
            - Generate AI response
            - Save AI response to database
            - Return response text
        """
        ...


class ChannelMessageHandlerRegistry:
    """Singleton registry for channel message handlers.

    Extensions register handlers via setup_message_handlers() hook.
    When extension is enabled, its handler automatically processes all channel messages.

    Thread-safe for handler registration during app startup.
    """

    def __init__(self):
        self._handlers: dict[str, ChannelMessageHandler] = {}
        self._default_handler: ChannelMessageHandler | None = None
        self._selected_handler: ChannelMessageHandler | None = None

    def register(self, extension_name: str, handler: ChannelMessageHandler) -> None:
        """Register a channel message handler for an extension.

        Note:
            Extensions should register handlers in setup_message_handlers() hook.
            Only one handler per extension is supported.
        """
        self._handlers[extension_name] = handler
        logger.info(
            f"Registered channel message handler: {handler.__class__.__name__} (extension: {extension_name})"
        )

    def set_default_handler(self, handler: ChannelMessageHandler) -> None:
        """Set default handler when no extension provides one."""
        self._default_handler = handler
        logger.info(
            f"Set default channel message handler: {handler.__class__.__name__}"
        )

    def finalize(self) -> None:
        """Select handler after all registrations complete. Call once at startup."""
        if self._handlers:
            if len(self._handlers) > 1:
                logger.warning(
                    f"Multiple channel message handlers registered: {list(self._handlers.keys())}. "
                    f"Using first. Consider enabling one extension or reorder ENABLED_EXTENSIONS."
                )
            extension_name, handler = next(iter(self._handlers.items()))
            self._selected_handler = handler
            logger.info(
                f"Using handler: {handler.__class__.__name__} (extension: {extension_name})"
            )
        elif self._default_handler:
            self._selected_handler = self._default_handler
            logger.info("Using default channel message handler")
        else:
            raise RuntimeError("No handler available - default handler not configured")

    def get_handler(self) -> ChannelMessageHandler:
        """Get the selected handler. Returns cached handler from finalize()."""
        if not self._selected_handler:
            raise RuntimeError(
                "Registry not finalized - call finalize() after registration"
            )
        return self._selected_handler


# Global singleton registry
channel_message_handler_registry = ChannelMessageHandlerRegistry()


def initialize_channel_message_handlers() -> None:
    """Initialize channel message handler system with default handler and extensions.

    Sets up the complete handler pipeline:
    1. Creates and registers default handler
    2. Loads extension handlers via setup_message_handlers() hook
    3. Finalizes handler selection
    """
    from app.extensions import load_extensions
    from app.lib.llm.factory import get_llm_provider

    from .channel_message_default import DefaultChannelMessageHandler

    # Initialize default handler
    llm_provider = get_llm_provider()
    default_handler = DefaultChannelMessageHandler(llm_provider)
    channel_message_handler_registry.set_default_handler(default_handler)

    # Load extension handlers
    load_extensions("message_handlers")

    # Finalize selection
    channel_message_handler_registry.finalize()
