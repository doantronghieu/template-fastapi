"""TypedDict definitions for Facebook Messenger webhook payloads.

Based on Facebook Messenger Platform Webhook Events documentation:
https://developers.facebook.com/docs/messenger-platform/reference/webhook-events

External API type hints for runtime type checking without validation overhead.
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


# Outgoing Message Types (Send API)


class QuickReplyDict(TypedDict, total=False):
    """Quick reply button structure for outgoing messages."""

    content_type: str  # "text", "user_phone_number", "user_email"
    title: str  # Button text (20 char limit, required for text type)
    payload: str  # Custom data sent to webhook (1000 char limit)
    image_url: str  # Optional icon image URL


class URLButtonDict(TypedDict, total=False):
    """URL button for templates."""

    type: str  # Always "web_url"
    title: str  # Button text (20 char limit)
    url: str  # URL to open in webview


class PostbackButtonDict(TypedDict, total=False):
    """Postback button for templates."""

    type: str  # Always "postback"
    title: str  # Button text (20 char limit)
    payload: str  # Custom data sent to webhook (1000 char limit)


class DefaultActionDict(TypedDict, total=False):
    """Default action when template is tapped."""

    type: str  # Always "web_url"
    url: str  # URL to open
    webview_height_ratio: str  # "compact", "tall", "full"


class GenericElementDict(TypedDict, total=False):
    """Single element in generic template (carousel item)."""

    title: str  # Element title (80 char limit)
    subtitle: str  # Element subtitle (80 char limit)
    image_url: str  # Image URL
    default_action: DefaultActionDict  # Action when element tapped
    buttons: list[URLButtonDict | PostbackButtonDict]  # Max 3 buttons
