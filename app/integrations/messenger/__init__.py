"""Facebook Messenger integration."""

from .client import MessengerClient
from .dependencies import MessengerClientDep, get_messenger_client
from .formatters import (
    format_quick_replies,
    format_template_buttons,
    format_template_elements,
)
from .schemas import Message, MultiMessageResponse
from .sender import (
    MessageSenderService,
    MessageSenderServiceDep,
    get_message_sender_service,
)
from .types import (
    ButtonType,
    MessageType,
    QuickReplyButton,
    QuickReplyContentType,
    TemplateButton,
    TemplateElement,
    WebhookPayload,
)
from .utils import format_messenger_message, format_response_for_storage
from .webhook import parse_webhook_payload

__all__ = [
    # Client and dependencies
    "MessengerClient",
    "MessengerClientDep",
    "get_messenger_client",
    # Sender service and dependencies
    "MessageSenderService",
    "MessageSenderServiceDep",
    "get_message_sender_service",
    # Types and enums (Messenger API constraints)
    "ButtonType",
    "MessageType",
    "QuickReplyContentType",
    "WebhookPayload",
    # Base Pydantic models for structured output
    "QuickReplyButton",
    "TemplateButton",
    "TemplateElement",
    # Base schemas with validation logic
    "Message",
    "MultiMessageResponse",
    # Formatters (Pydantic → Messenger API)
    "format_quick_replies",
    "format_template_buttons",
    "format_template_elements",
    # Utilities
    "format_messenger_message",
    "format_response_for_storage",
    "parse_webhook_payload",
]
