from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Column, String
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseTable, uuid_fk

if TYPE_CHECKING:
    from .user import User


class MessageSenderRole(str, Enum):
    """Message sender role enumeration."""

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
        description="External channel conversation ID (Telegram chat ID, WhatsApp thread, etc.)",
    )
    ai_summary: str | None = Field(
        default=None,
        max_length=10000,
        description="AI-generated summary of the conversation for admin quick reference",
    )


class MessageBase(SQLModel):
    """Base message fields for schemas."""

    sender_role: MessageSenderRole = Field(
        description="Who sent the message: client, ai, or admin"
    )
    content: str = Field(max_length=10000, description="Message text content")


class Conversation(ConversationBase, BaseTable, table=True):
    """Conversation model for tracking user conversations."""

    __tablename__ = "conversations"

    # Override channel_conversation_id to add index and unique constraint
    channel_conversation_id: str | None = Field(
        default=None,
        index=True,
        unique=True,
        max_length=255,
        description="External channel conversation ID (Telegram chat ID, WhatsApp thread, etc.)",
    )

    # Table-specific fields not in ConversationBase
    ai_summary_updated_at: datetime | None = Field(
        default=None, description="Timestamp when AI summary was last generated"
    )
    user_id: UUID = uuid_fk("users")

    # Relationships
    messages: list["Message"] = Relationship(back_populates="conversation")
    user: "User" = Relationship(back_populates="conversations")


class Message(MessageBase, BaseTable, table=True):
    """Message model for conversation messages."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            f"sender_role IN ({', '.join(repr(r.value) for r in MessageSenderRole)})",
            name="valid_sender_role",
        ),
    )

    # Table-specific fields not in MessageBase
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
