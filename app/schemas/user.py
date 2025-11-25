"""User request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class UserBase(BaseModel):
    """Base schema with common user field definitions."""

    email: str | None = Field(None, description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User display name")
    role: str = Field(..., description="User role: admin, employee, client, or ai")
    profile: dict = Field(default_factory=dict, description="Additional user profile data")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating an existing user (partial update)."""

    email: str | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = None
    profile: dict | None = None


# Response schemas
class UserChannelResponse(BaseModel):
    """User channel information."""

    id: UUID
    channel_id: str
    channel_type: str
    is_primary: bool


class UserResponseBase(BaseModel):
    """Minimal user response for nested API responses."""

    id: UUID
    name: str
    role: str


class UserDetailResponse(UserResponseBase):
    """Detailed user response with all public fields."""

    email: str | None
    created_at: datetime
    updated_at: datetime


class UserFullResponse(UserDetailResponse):
    """Full user response with profile and channels."""

    profile: dict
    channels: list[UserChannelResponse]
