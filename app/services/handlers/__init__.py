"""Channel message handlers package.

Provides extensible message handling for messaging channels (Messenger, WhatsApp, Telegram).
Extensions can register custom handlers to override default AI response generation.
"""

from app.services.handlers.channel_message_default import (
    DefaultChannelMessageHandler,
)
from app.services.handlers.channel_message_registry import (
    ChannelMessageHandler,
    ChannelMessageHandlerRegistry,
    channel_message_handler_registry,
    initialize_channel_message_handlers,
)

__all__ = [
    "ChannelMessageHandler",
    "ChannelMessageHandlerRegistry",
    "DefaultChannelMessageHandler",
    "channel_message_handler_registry",
    "initialize_channel_message_handlers",
]
