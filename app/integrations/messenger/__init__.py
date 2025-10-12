"""Facebook Messenger integration."""

from .client import MessengerClient
from .dependencies import MessengerClientDep, get_messenger_client
from .types import WebhookPayload
from .webhook import parse_webhook_payload

__all__ = [
    "MessengerClient",
    "MessengerClientDep",
    "WebhookPayload",
    "get_messenger_client",
    "parse_webhook_payload",
]
