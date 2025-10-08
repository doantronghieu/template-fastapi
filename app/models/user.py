from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from .base import timestamp_field, uuid_fk, uuid_pk

if TYPE_CHECKING:
    from .messaging import Conversation, Message


class ChannelType(str, Enum):
    """Channel type enumeration."""

    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    DIRECT = "direct"


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    EMPLOYEE = "employee"
    CLIENT = "client"
    AI = "ai"


class UserChannel(SQLModel, table=True):
    """User channel model for mapping external channel IDs to users."""

    __tablename__ = "user_channels"
    __table_args__ = (
        UniqueConstraint("channel_id", "channel_type", name="unique_channel_per_type"),
        CheckConstraint(
            f"channel_type IN ({', '.join(repr(c.value) for c in ChannelType)})",
            name="valid_channel_type",
        ),
    )

    id: UUID = uuid_pk()
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field()

    user_id: UUID = uuid_fk("users")
    channel_id: str = Field(
        index=True,
        max_length=255,
        description="External channel identifier (e.g., Telegram user ID, WhatsApp number)",
    )
    channel_type: ChannelType = Field(
        sa_column=Column(String(50), nullable=False),
        description="Channel platform type (telegram, whatsapp, messenger, direct)",
    )
    is_primary: bool = Field(
        default=False, description="Whether this is the user's primary channel"
    )

    # Relationships
    user: "User" = Relationship(back_populates="channels")


class User(SQLModel, table=True):
    """User model with role-based access."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            f"role IN ({', '.join(repr(r.value) for r in UserRole)})",
            name="valid_user_role",
        ),
    )

    id: UUID = uuid_pk()
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field()

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
