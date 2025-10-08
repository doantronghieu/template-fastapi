from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Column, String
from sqlmodel import Field, Relationship, SQLModel

from .base import timestamp_field, uuid_fk, uuid_pk

if TYPE_CHECKING:
    from .user import User


class MessageSenderRole(str, Enum):
    """Message sender role enumeration."""

    CLIENT = "client"
    AI = "ai"
    ADMIN = "admin"


class ConversationBase(SQLModel):
    """Base conversation fields with descriptions."""

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


class Conversation(ConversationBase, table=True):
    """Conversation model for tracking user conversations."""

    __tablename__ = "conversations"

    id: UUID = uuid_pk()
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field()

    user_id: UUID = uuid_fk("users")
    channel_conversation_id: str | None = Field(
        default=None, index=True, unique=True, max_length=255
    )  # Override to add index and unique constraint

    # Relationships
    messages: list["Message"] = Relationship(back_populates="conversation")
    user: "User" = Relationship(back_populates="conversations")


class MessageBase(SQLModel):
    """Base message fields with descriptions."""

    sender_role: MessageSenderRole = Field(
        description="Who sent the message: client, ai, or admin"
    )
    content: str = Field(max_length=10000, description="Message text content")


class Message(MessageBase, table=True):
    """Message model for conversation messages."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            f"sender_role IN ({', '.join(repr(r.value) for r in MessageSenderRole)})",
            name="valid_sender_role",
        ),
    )

    id: UUID = uuid_pk()
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field()

    conversation_id: UUID = uuid_fk("conversations")
    user_id: UUID = uuid_fk("users")
    sender_role: MessageSenderRole = Field(
        sa_column=Column(String(50), nullable=False)
    )  # Override to add sa_column

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    user: "User" = Relationship(back_populates="messages")
