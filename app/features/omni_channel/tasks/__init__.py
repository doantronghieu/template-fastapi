"""Task exports for omni-channel feature.

Tasks are auto-discovered by Celery via include config.
Handler initialization runs when this module is loaded.
"""

from app.core.config import settings

from .channel_tasks import process_messenger_message, send_messenger_special_message

__all__ = [
    "process_messenger_message",
    "send_messenger_special_message",
]

# Initialize channel message handlers when Celery loads this module
if "messenger" in settings.ENABLED_INTEGRATIONS:
    from ..handlers import initialize_channel_message_handlers

    initialize_channel_message_handlers()
