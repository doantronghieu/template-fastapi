"""Type definitions for Facebook Messenger webhook payloads.

Based on Facebook Messenger Platform Webhook Events documentation:
https://developers.facebook.com/docs/messenger-platform/reference/webhook-events
"""

from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field, model_validator


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


# Enums for Messenger API constraints


class MessageType(str, Enum):
    """Type of message component in AI response.

    Corresponds to Messenger Send API message types.
    """

    TEXT = "text"
    QUICK_REPLY = "quick_reply"
    TEMPLATE = "template"


class ButtonType(str, Enum):
    """Button type for templates.

    Messenger API button types for generic templates.
    """

    WEB_URL = "web_url"
    POSTBACK = "postback"


class QuickReplyContentType(str, Enum):
    """Quick reply content type (Messenger constraint).

    Valid content_type values for quick reply buttons.
    """

    TEXT = "text"
    USER_PHONE_NUMBER = "user_phone_number"
    USER_EMAIL = "user_email"


# Pydantic models for structured output (base classes)


class QuickReplyButton(BaseModel):
    """Quick reply button for Messenger (max 11 per message).

    Messenger API constraints and limits.
    """

    title: str = Field(
        ...,
        max_length=20,
        description="Button text (max 20 chars)",
    )
    payload: str = Field(
        ...,
        max_length=1000,
        description="Custom data sent to webhook (max 1000 chars)",
    )
    content_type: QuickReplyContentType = Field(
        default=QuickReplyContentType.TEXT,
        description="Content type (text, phone, email)",
    )
    image_url: str | None = Field(
        default=None,
        description="Optional icon image URL",
    )


class TemplateButton(BaseModel):
    """Button for generic template elements (max 3 per element).

    Messenger API button types and constraints.
    """

    type: ButtonType = Field(
        ...,
        description="Button type: web_url or postback",
    )
    title: str = Field(
        ...,
        max_length=20,
        description="Button text (max 20 chars)",
    )
    url: str | None = Field(
        default=None,
        description="URL for web_url type buttons",
    )
    payload: str | None = Field(
        default=None,
        max_length=1000,
        description="Payload for postback type buttons (max 1000 chars)",
    )

    @model_validator(mode="after")
    def validate_button_data(self) -> "TemplateButton":
        """Ensure url/payload match button type (Messenger API requirement)."""
        if self.type == ButtonType.WEB_URL and not self.url:
            raise ValueError("web_url button requires url field")
        if self.type == ButtonType.POSTBACK and not self.payload:
            raise ValueError("postback button requires payload field")
        return self


class TemplateElement(BaseModel):
    """Element in generic template carousel (max 10 per message).

    Messenger API generic template structure and constraints.
    """

    title: str = Field(
        ...,
        max_length=80,
        description="Element title (max 80 chars)",
    )
    subtitle: str | None = Field(
        default=None,
        max_length=80,
        description="Element subtitle (max 80 chars)",
    )
    image_url: str | None = Field(
        default=None,
        description="Image URL for visual display",
    )
    buttons: list[TemplateButton] | None = Field(
        default=None,
        max_length=3,
        description="Action buttons (max 3 per element)",
    )

    @model_validator(mode="after")
    def validate_element_content(self) -> "TemplateElement":
        """Messenger requires at least one of: subtitle, image_url, or buttons."""
        if not self.subtitle and not self.image_url and not self.buttons:
            raise ValueError(
                "Element must have at least one of: subtitle, image_url, or buttons"
            )
        return self
