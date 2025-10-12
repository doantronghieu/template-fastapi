"""Type definitions for Facebook Messenger webhook payloads.

Based on Facebook Messenger Platform Webhook Events documentation:
https://developers.facebook.com/docs/messenger-platform/reference/webhook-events
"""

from typing import TypedDict


class Sender(TypedDict, total=False):
    """Webhook sender information."""

    id: str  # Page-Scoped ID (PSID)


class Recipient(TypedDict, total=False):
    """Webhook recipient information."""

    id: str  # Page ID


class AttachmentPayload(TypedDict, total=False):
    """Attachment payload data."""

    url: str  # Media URL
    title: str  # File title/name
    sticker_id: int  # Sticker ID


class Attachment(TypedDict, total=False):
    """Message attachment structure."""

    type: str  # "image", "video", "audio", "file", "template", "fallback"
    payload: AttachmentPayload


class Message(TypedDict, total=False):
    """Message data structure."""

    mid: str  # Message ID
    text: str  # Message text content
    attachments: list[Attachment]  # Media attachments
    quick_reply: dict  # Quick reply payload
    reply_to: dict  # Reply context


class Postback(TypedDict, total=False):
    """Postback event data."""

    title: str  # Button title
    payload: str  # Developer-defined payload
    referral: dict  # Referral information


class Messaging(TypedDict, total=False):
    """Individual messaging event."""

    sender: Sender
    recipient: Recipient
    timestamp: int  # Unix timestamp in milliseconds
    message: Message
    postback: Postback
    delivery: dict  # Message delivery confirmation
    read: dict  # Message read confirmation


class Entry(TypedDict, total=False):
    """Webhook entry containing messaging events."""

    id: str  # Page ID
    time: int  # Unix timestamp
    messaging: list[Messaging]


class WebhookPayload(TypedDict, total=False):
    """Complete webhook payload structure."""

    object: str  # Always "page" for Messenger
    entry: list[Entry]
