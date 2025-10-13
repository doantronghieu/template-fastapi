"""Messenger request/response schemas."""

from pydantic import BaseModel, Field, model_validator


class SendMessageRequest(BaseModel):
    """Send a message to a Messenger user."""

    recipient_id: str = Field(..., description="Facebook Page-Scoped ID (PSID)")
    text: str = Field(..., max_length=2000, description="Message text to send")


class SendMessageResponse(BaseModel):
    """Response from sending a message."""

    recipient_id: str
    message_id: str


# Quick Replies Schemas


class QuickReplyButton(BaseModel):
    """Quick reply button (max 13 per message)."""

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
    quick_replies: list[QuickReplyButton] = Field(
        ..., max_length=13, description="Quick reply buttons (max 13)"
    )


# Generic Template Schemas


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
