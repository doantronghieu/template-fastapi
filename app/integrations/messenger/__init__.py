"""Facebook Messenger integration."""

from .client import MessengerClient
from .dependencies import MessengerClientDep, get_messenger_client
from .types import WebhookPayload
from .utils import format_messenger_message
from .webhook import parse_webhook_payload

__all__ = [
    "MessengerClient",
    "MessengerClientDep",
    "WebhookPayload",
    "format_messenger_message",
    "get_messenger_client",
    "parse_webhook_payload",
]
