"""Pydantic models for LLM structured output.

Messenger-specific models with validation for AI-generated responses.
Extensions can inherit and add domain-specific field descriptions.
"""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


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
