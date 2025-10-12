"""Webhook payload parsing for Facebook Messenger.

Normalizes Facebook's nested webhook structure into flat message events.
"""

import logging

from .types import WebhookPayload

logger = logging.getLogger(__name__)


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


def parse_webhook_payload(data: WebhookPayload) -> list[dict]:
    """
    Parse Facebook Messenger webhook payload into normalized message events.

    Facebook sends nested structure: entry → messaging → sender/message.
    This flattens it into simple dicts with sender_id, message_text, conversation_id.

    Args:
        data: Webhook payload from Facebook (see types.py for structure)

    Returns:
        List of normalized message events ready for processing

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

            message = messaging.get("message", {})
            message_text = message.get("text")
            attachments = message.get("attachments", [])

            # Helper to create event dict
            def create_event(text: str) -> dict:
                return {
                    "sender_id": sender_id,
                    "message_text": text,
                    "conversation_id": sender_id,
                }

            # Process text content if present
            if message_text:
                events.append(create_event(message_text))

            # Process attachments (message can have both text AND attachments)
            events.extend(create_event(_format_attachment(att)) for att in attachments)

    return events
