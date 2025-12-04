"""Messaging request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlmodel import SQLModel

from ..models import ChannelType, ConversationBase, MessageBase
from .user import UserResponseBase


class ChannelModeBase(SQLModel):
    """Base schema for channel mode parameters.

    Used when messages/conversations come from external channels.
    """

    channel_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="External channel user ID",
    )
    channel_type: ChannelType | None = Field(
        None,
        description="Channel platform type",
    )
    channel_conversation_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="External conversation ID",
    )


class InternalModeBase(SQLModel):
    """Base schema for internal mode parameters.

    Used for direct API access with internal UUIDs.
    """

    user_id: UUID | None = Field(None, description="Internal user UUID")
    conversation_id: UUID | None = Field(None, description="Internal conversation UUID")


class MessageCreate(MessageBase, ChannelModeBase, InternalModeBase):
    """Request schema for creating a message."""

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v

    @model_validator(mode="after")
    def validate_mode_parameters(self) -> "MessageCreate":
        """Validate that either channel mode or internal mode parameters are provided."""
        is_channel_mode = self.channel_id is not None and self.channel_type is not None
        is_internal_mode = self.user_id is not None and self.conversation_id is not None

        if not is_channel_mode and not is_internal_mode:
            raise ValueError(
                "Must provide either (channel_id + channel_type) or (user_id + conversation_id)"
            )

        return self


class MessageResponse(MessageBase):
    """Response schema for a single message."""

    id: UUID
    created_at: datetime
    user_id: UUID
    conversation_id: UUID


class MessagePreviewResponse(MessageBase):
    """Message preview for conversation lists."""

    created_at: datetime


class MessageHistoryItem(BaseModel):
    """Single message in conversation history."""

    role: str
    content: str
    created_at: str


class ConversationHistoryResponse(BaseModel):
    """Response schema with formatted conversation history."""

    conversation_id: UUID
    conversation_history: list[MessageHistoryItem]
    next_cursor: UUID | None = None


class ConversationListItem(ConversationBase):
    """Response schema for a single conversation in list."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    ai_summary_updated_at: datetime | None
    user: UserResponseBase
    channel_type: str | None
    last_message: MessagePreviewResponse | None


class ConversationListResponse(BaseModel):
    """Response schema for conversation list."""

    conversations: list[ConversationListItem]
    next_cursor: UUID | None = None
    has_more: bool


class ConversationMessagesQuery(BaseModel):
    """Request body for retrieving conversation messages."""

    conversation_id: UUID | None = Field(None, description="Internal conversation UUID")
    channel_conversation_id: str | None = Field(
        None, description="External conversation identifier"
    )
    limit: int = Field(
        50, ge=1, le=100, description="Maximum number of messages to return"
    )
    before_message_id: UUID | None = Field(
        None, description="Message UUID to fetch messages before (pagination)"
    )
    order: str = Field(
        "created_at.desc",
        description="Sort order: 'field.direction' (e.g., 'created_at.desc')",
    )
    reverse: bool = Field(
        True, description="Reverse the final result order after sorting"
    )

    @model_validator(mode="after")
    def validate_at_least_one_identifier(self) -> "ConversationMessagesQuery":
        """Validate that at least one identifier is provided."""
        if not self.conversation_id and not self.channel_conversation_id:
            raise ValueError("Must provide conversation_id or channel_conversation_id")
        return self
