"""Facebook Messenger integration."""

from fastapi import APIRouter

from .client import MessengerClient
from .dependencies import MessengerClientDep, get_messenger_client
from .schemas import Message, MultiMessageResponse
from .services.sender import (
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
from .utils.formatters import (
    format_quick_replies,
    format_template_buttons,
    format_template_elements,
)
from .utils.webhook_parser import (
    format_messenger_message,
    format_response_for_storage,
    parse_webhook_payload,
)

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


def setup_api(integration_router: APIRouter) -> None:
    """Setup API endpoints for Messenger integration.

    Args:
        integration_router: Main integration router to attach Messenger endpoints
    """
    from . import api

    integration_router.include_router(
        api.router,
        prefix="/messenger",
        tags=["Messenger Integration"],
    )


def setup_webhooks(webhook_router: APIRouter) -> None:
    """Setup webhook endpoints for Messenger integration.

    Args:
        webhook_router: Main webhook router to attach Messenger webhook handlers
    """
    from . import webhooks

    webhook_router.include_router(
        webhooks.router,
        prefix="/messenger",
    )
