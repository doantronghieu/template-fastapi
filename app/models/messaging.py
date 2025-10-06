from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import timestamp_field, uuid_fk, uuid_pk

if TYPE_CHECKING:
    from .user import User


class Conversation(SQLModel, table=True):
    """Conversation model for tracking user conversations."""

    __tablename__ = "conversations"

    id: UUID = uuid_pk()
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field()

    title: str | None = Field(max_length=500)
    user_id: UUID = uuid_fk("users")

    # Relationships
    messages: list["Message"] = Relationship(back_populates="conversation")
    user: "User" = Relationship(back_populates="conversations")


class Message(SQLModel, table=True):
    """Message model for conversation messages."""

    __tablename__ = "messages"

    id: UUID = uuid_pk()
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field()

    conversation_id: UUID = uuid_fk("conversations")
    user_id: UUID = uuid_fk("users")
    content: str = Field(max_length=10000)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    user: "User" = Relationship(back_populates="messages")
