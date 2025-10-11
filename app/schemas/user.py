"""User response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
