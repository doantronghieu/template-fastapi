"""Base Pydantic schemas for Messenger structured output.

Provides base classes with Messenger API validation logic.
Extensions can inherit and add domain-specific field descriptions.
"""

from pydantic import BaseModel, Field, model_validator

from .types import MessageType, QuickReplyButton, TemplateElement


class Message(BaseModel):
    """Base message component with Messenger API validation.

    Validates required fields based on message type per Messenger API requirements.
    Extensions should inherit and override fields with domain-specific descriptions.
    """

    type: MessageType = Field(
        ...,
        description="Message type: text, quick_reply, or template",
    )
    text: str | None = Field(
        default=None,
        max_length=2000,
        description="Message text content (max 2000 chars)",
    )
    quick_replies: list[QuickReplyButton] | None = Field(
        default=None,
        max_length=13,
        description="Quick reply buttons (max 13)",
    )
    template_elements: list[TemplateElement] | None = Field(
        default=None,
        max_length=10,
        description="Template carousel elements (max 10)",
    )

    @model_validator(mode="after")
    def validate_message_structure(self) -> "Message":
        """Validate required fields based on message type.

        Messenger API requirements:
        - TEXT: requires text field
        - QUICK_REPLY: requires text AND quick_replies
        - TEMPLATE: requires template_elements
        """
        if self.type == MessageType.TEXT:
            if not self.text:
                raise ValueError("text type requires non-empty text field")

        elif self.type == MessageType.QUICK_REPLY:
            if not self.text:
                raise ValueError("quick_reply type requires non-empty text field")
            if not self.quick_replies or len(self.quick_replies) == 0:
                raise ValueError(
                    "quick_reply type requires non-empty quick_replies list"
                )

        elif self.type == MessageType.TEMPLATE:
            if not self.template_elements or len(self.template_elements) == 0:
                raise ValueError(
                    "template type requires non-empty template_elements list"
                )

        return self


class MultiMessageResponse(BaseModel):
    """Base response with multiple message components.

    Enforces Messenger API constraints on message combinations.
    Extensions should inherit and use domain-specific Message subclass.
    """

    messages: list[Message] = Field(
        ...,
        min_length=1,
        description="Array of sequential messages",
    )

    @model_validator(mode="after")
    def validate_message_constraints(self) -> "MultiMessageResponse":
        """Validate Messenger API constraints across messages.

        Messenger best practices:
        - Maximum 1 quick_reply per response
        - Maximum 1 template per response
        - Multiple text messages allowed
        """
        quick_reply_count = sum(
            1 for m in self.messages if m.type == MessageType.QUICK_REPLY
        )
        template_count = sum(1 for m in self.messages if m.type == MessageType.TEMPLATE)

        if quick_reply_count > 1:
            raise ValueError("Response can have at most 1 quick_reply message")
        if template_count > 1:
            raise ValueError("Response can have at most 1 template message")

        return self


# API Request/Response Schemas


class SendMessageRequest(BaseModel):
    """Send a message to a Messenger user."""

    recipient_id: str = Field(..., description="Facebook Page-Scoped ID (PSID)")
    text: str = Field(..., max_length=2000, description="Message text to send")


class SendMessageResponse(BaseModel):
    """Response from sending a message."""

    recipient_id: str
    message_id: str


# Quick Replies API Schemas


class QuickReplyButtonAPI(BaseModel):
    """Quick reply button for API (max 13 per message)."""

    content_type: str = Field(
        "text", description="Button type: text, user_phone_number, user_email"
    )
    title: str = Field(..., max_length=20, description="Button text")
    payload: str = Field("", max_length=1000, description="Custom data sent to webhook")
    image_url: str | None = Field(None, description="Optional button icon URL")


class SendQuickRepliesRequest(BaseModel):
    """Send quick replies to a Messenger user."""

    recipient_id: str = Field(..., description="Facebook Page-Scoped ID (PSID)")
    text: str = Field(..., max_length=2000, description="Message text above buttons")
    quick_replies: list[QuickReplyButtonAPI] = Field(
        ..., max_length=13, description="Quick reply buttons (max 13)"
    )


# Generic Template API Schemas


class URLButton(BaseModel):
    """URL button for templates."""

    type: str = Field("web_url", description="Button type")
    title: str = Field(..., max_length=20, description="Button text")
    url: str = Field(..., description="URL to open in webview")


class PostbackButton(BaseModel):
    """Postback button for templates."""

    type: str = Field("postback", description="Button type")
    title: str = Field(..., max_length=20, description="Button text")
    payload: str = Field(
        ..., max_length=1000, description="Custom data sent to webhook"
    )


class GenericElement(BaseModel):
    """Element in generic template (carousel item)."""

    title: str = Field(..., max_length=80, description="Element title")
    subtitle: str | None = Field(None, max_length=80, description="Element subtitle")
    image_url: str | None = Field(None, description="Image URL")
    buttons: list[URLButton | PostbackButton] | None = Field(
        None, max_length=3, description="Action buttons (max 3)"
    )

    @model_validator(mode="after")
    def validate_element_content(self) -> "GenericElement":
        """Facebook requires at least one of: subtitle, image_url, or buttons."""
        if not self.subtitle and not self.image_url and not self.buttons:
            raise ValueError(
                "Element must have at least one of: subtitle, image_url, or buttons"
            )
        return self


class SendGenericTemplateRequest(BaseModel):
    """Send generic template (single card or carousel)."""

    recipient_id: str = Field(..., description="Facebook Page-Scoped ID (PSID)")
    elements: list[GenericElement] = Field(
        ..., min_length=1, max_length=10, description="Template elements (1-10)"
    )
