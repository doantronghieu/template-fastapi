"""Webhook payload parsing and message formatting utilities for Facebook Messenger."""

import logging
from typing import Any

from ..types import WebhookPayload

logger = logging.getLogger(__name__)


def parse_webhook_payload(data: WebhookPayload) -> list[dict]:
    """
    Parse Facebook Messenger webhook payload into normalized events.

    Facebook sends nested structure: entry → messaging → sender/message/postback.
    This flattens it into simple dicts for processing.

    Args:
        data: Webhook payload from Facebook (see types.py for structure)

    Returns:
        List of normalized events with event_type discriminator

    Event types:
        - message: Text or attachment from user
        - postback: Button click from user

    Note:
        - Attachments are converted to descriptive text (e.g., "[User sent an image]")
        - Each message can have both text and attachments (processed separately)
        - Uses sender_id as conversation_id (1:1 mapping for Messenger)
    """
    events = []

    # Facebook payload structure: entry (page) → messaging (events)
    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging.get("sender", {}).get("id")
            if not sender_id:
                logger.debug("Skip: no sender_id")
                continue

            # Check for message event
            message = messaging.get("message", {})
            if message:
                message_text = message.get("text")
                attachments = message.get("attachments", [])

                # Helper to create message event dict
                def create_message_event(text: str) -> dict:
                    return {
                        "event_type": "message",
                        "sender_id": sender_id,
                        "message_text": text,
                        "conversation_id": sender_id,
                    }

                # Process text content if present
                if message_text:
                    events.append(create_message_event(message_text))

                # Process attachments (message can have both text AND attachments)
                events.extend(
                    create_message_event(_format_attachment(att)) for att in attachments
                )

            # Check for postback event (button click)
            postback = messaging.get("postback", {})
            if postback:
                events.append(
                    {
                        "event_type": "postback",
                        "sender_id": sender_id,
                        "payload": postback.get("payload", ""),
                        "title": postback.get("title", ""),
                        "conversation_id": sender_id,
                    }
                )

    return events


def _format_attachment(attachment: dict) -> str:
    """
    Convert attachment to descriptive text for LLM context.

    Args:
        attachment: Attachment dict from Facebook webhook

    Returns:
        Formatted message describing the attachment
    """
    attachment_type = attachment.get("type")

    if attachment_type == "image":
        return "[User sent an image]"
    elif attachment_type in ["video", "audio", "file"]:
        filename = attachment.get("payload", {}).get("title", "unknown")
        return f"[User sent a file: {filename}]"
    else:
        return f"[User sent {attachment_type}]"


def format_messenger_message(
    message_type: str, text: str | None = None, **kwargs
) -> str:
    """
    Format Messenger message data into human-readable text for database storage.

    Converts rich message types (quick_replies, generic_template, postback)
    into descriptive text that provides context for LLM conversation history.

    Args:
        message_type: Type of message ("text", "quick_replies", "generic_template", "postback")
        text: Main message text (for text and quick_replies types)
        **kwargs: Type-specific data (quick_replies, elements, payload, title)

    Returns:
        Formatted string for content field

    Examples:
        >>> format_messenger_message("text", text="Hello!")
        "Hello!"

        >>> format_messenger_message("quick_replies", text="Choose color",
        ...     quick_replies=[{"title": "Red"}, {"title": "Blue"}])
        "Choose color [Options: Red, Blue]"

        >>> format_messenger_message("generic_template",
        ...     elements=[{"title": "Product 1"}, {"title": "Product 2"}])
        "[Sent 2 cards: Product 1, Product 2]"

        >>> format_messenger_message("postback", title="Buy Now", payload="PRODUCT_123")
        "[User clicked: Buy Now - PRODUCT_123]"
    """
    if message_type == "text":
        return text or ""

    if message_type == "quick_replies":
        quick_replies = kwargs.get("quick_replies", [])
        options = ", ".join(
            qr.get("title", "") for qr in quick_replies if qr.get("title")
        )
        return f"{text} [Options: {options}]" if options else text or ""

    if message_type == "generic_template":
        elements = kwargs.get("elements", [])
        count = len(elements)
        titles = ", ".join(elem.get("title", "") for elem in elements[:3])
        if count > 3:
            titles += f", ... ({count - 3} more)"
        card_label = "card" if count == 1 else "cards"
        return f"[Sent {count} {card_label}: {titles}]"

    if message_type == "postback":
        title = kwargs.get("title", "")
        payload = kwargs.get("payload", "")
        return f"[User clicked: {title} - {payload}]"

    return text or ""


def format_response_for_storage(response: Any) -> str:
    """Format multi-message response for database storage.

    Works with any response object that has a .messages attribute following
    the MultiMessageResponseProtocol (duck typing).

    Args:
        response: Response object with .messages attribute containing message components

    Returns:
        Human-readable formatted string combining all messages

    Example:
        >>> response = AIResponse(messages=[...])
        >>> formatted = format_response_for_storage(response)
        "Hello! [Options: Location A, Location B]"
    """
    from app.integrations.messenger.types import MessageType

    formatted_parts = []

    for msg in response.messages:
        if msg.type == MessageType.TEXT:
            formatted_parts.append(msg.text)

        elif msg.type == MessageType.QUICK_REPLY:
            formatted = format_messenger_message(
                message_type="quick_replies",
                text=msg.text,
                quick_replies=[{"title": qr.title} for qr in msg.quick_replies],
            )
            formatted_parts.append(formatted)

        elif msg.type == MessageType.TEMPLATE:
            formatted = format_messenger_message(
                message_type="generic_template",
                elements=[{"title": elem.title} for elem in msg.template_elements],
            )
            formatted_parts.append(formatted)

    return "\n\n".join(formatted_parts)
