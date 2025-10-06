from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from .base import timestamp_field, uuid_pk

if TYPE_CHECKING:
    from .messaging import Conversation, Message


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    EMPLOYEE = "employee"
    CLIENT = "client"
    AI = "ai"


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

    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=255)
    role: str = Field(max_length=50)
    profile: dict = Field(default_factory=dict, sa_column=Column(JSONB))

    # Relationships
    conversations: list["Conversation"] = Relationship(back_populates="user")
    messages: list["Message"] = Relationship(back_populates="user")
