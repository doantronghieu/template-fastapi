"""Omni-channel models for multi-channel messaging.

Contains User, UserChannel, Conversation, Message models and related enums.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import BaseTable, uuid_fk

if TYPE_CHECKING:
    pass


class ChannelType(str, Enum):
    """Supported messaging channel types."""

    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    ZALO = "zalo"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    DIRECT = "direct"


class UserRole(str, Enum):
    """User role types."""

    ADMIN = "admin"
    EMPLOYEE = "employee"
    CLIENT = "client"
    AI = "ai"


class MessageSenderRole(str, Enum):
    """Message sender role for conversation history."""

    CLIENT = "client"
    AI = "ai"
    ADMIN = "admin"


class ConversationBase(SQLModel):
    """Base conversation fields for schemas."""

    title: str | None = Field(
        default=None,
        max_length=500,
        description="Conversation title or auto-generated name",
    )
    channel_conversation_id: str | None = Field(
        default=None,
        max_length=255,
        description="External channel conversation ID",
    )
    ai_summary: str | None = Field(
        default=None,
        max_length=10000,
        description="AI-generated summary for admin quick reference",
    )


class MessageBase(SQLModel):
    """Base message fields for schemas."""

    sender_role: MessageSenderRole = Field(
        description="Who sent the message: client, ai, or admin"
    )
    content: str = Field(max_length=10000, description="Message text content")


class UserChannel(BaseTable, table=True):
    """Links users to messaging channels (Telegram, WhatsApp, etc.)."""

    __tablename__ = "user_channels"
    __table_args__ = (
        UniqueConstraint("channel_id", "channel_type", name="unique_channel_per_type"),
        CheckConstraint(
            f"channel_type IN ({', '.join(repr(c.value) for c in ChannelType)})",
            name="valid_channel_type",
        ),
    )

    user_id: UUID = uuid_fk("users")
    channel_id: str = Field(
        index=True,
        max_length=255,
        description="External channel identifier (e.g., Telegram user ID)",
    )
    channel_type: ChannelType = Field(
        sa_column=Column(String(50), nullable=False),
        description="Channel platform type",
    )
    is_primary: bool = Field(
        default=False, description="Whether this is user's primary channel"
    )

    # Relationships
    user: "User" = Relationship(back_populates="channels")


class User(BaseTable, table=True):
    """User model supporting both email and channel-based users."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            f"role IN ({', '.join(repr(r.value) for r in UserRole)})",
            name="valid_user_role",
        ),
    )

    email: str | None = Field(
        default=None,
        unique=True,
        index=True,
        max_length=255,
        description="User email address (unique, optional for channel-only users)",
    )
    name: str = Field(max_length=255, description="User display name")
    role: str = Field(
        max_length=50, description="User role: admin, employee, client, or ai"
    )
    profile: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Additional user profile data stored as JSONB",
    )

    # Relationships
    channels: list["UserChannel"] = Relationship(back_populates="user")
    conversations: list["Conversation"] = Relationship(back_populates="user")
    messages: list["Message"] = Relationship(back_populates="user")


class Conversation(ConversationBase, BaseTable, table=True):
    """Conversation model with support for AI summaries."""

    __tablename__ = "conversations"

    # Override channel_conversation_id to add index and unique constraint
    channel_conversation_id: str | None = Field(
        default=None,
        index=True,
        unique=True,
        max_length=255,
        description="External channel conversation ID",
    )

    # Table-specific fields
    ai_summary_updated_at: datetime | None = Field(
        default=None, description="Timestamp when AI summary was last generated"
    )
    user_id: UUID = uuid_fk("users")

    # Relationships
    messages: list["Message"] = Relationship(back_populates="conversation")
    user: "User" = Relationship(back_populates="conversations")


class Message(MessageBase, BaseTable, table=True):
    """Individual message in a conversation."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            f"sender_role IN ({', '.join(repr(r.value) for r in MessageSenderRole)})",
            name="valid_sender_role",
        ),
    )

    # Table-specific fields
    conversation_id: UUID = uuid_fk("conversations")
    user_id: UUID = uuid_fk("users")

    # Override sender_role to add sa_column for enum handling
    sender_role: MessageSenderRole = Field(
        sa_column=Column(String(50), nullable=False),
        description="Who sent the message: client, ai, or admin",
    )

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    user: "User" = Relationship(back_populates="messages")
