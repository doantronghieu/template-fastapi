"""Voice feature API schemas.

Request and response models for voice API endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.features.voice.models import (
    VoiceMessageRole,
    VoiceSessionStatus,
    VoiceSessionType,
)


# === Session Schemas ===


class VoiceSessionCreate(BaseModel):
    """Request to create a new voice session."""

    session_type: VoiceSessionType = Field(
        default=VoiceSessionType.WEB,
        description="Type of voice session",
    )
    provider_type: str = Field(
        default="livekit",
        description="Provider identifier",
    )
    external_session_id: str | None = Field(
        default=None,
        description="Optional external ID (auto-generated if not provided)",
    )
    from_number: str | None = Field(
        default=None,
        description="Caller phone number for phone sessions",
    )
    to_number: str | None = Field(
        default=None,
        description="Called phone number for phone sessions",
    )


class VoiceSessionResponse(BaseModel):
    """Voice session response."""

    id: UUID
    external_session_id: str
    provider_type: str
    session_type: VoiceSessionType
    status: VoiceSessionStatus
    from_number: str | None = None
    to_number: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int | None = None  # Computed property
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VoiceSessionStatusUpdate(BaseModel):
    """Request to update session status."""

    status: VoiceSessionStatus


# === Message Schemas ===


class VoiceMessageCreate(BaseModel):
    """Request to add a message to a session."""

    role: VoiceMessageRole
    content: str


class VoiceMessageResponse(BaseModel):
    """Voice message response."""

    id: UUID
    session_id: UUID
    role: VoiceMessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# === List Schemas ===


class VoiceSessionListParams(BaseModel):
    """Parameters for listing voice sessions."""

    limit: int = Field(default=10, ge=1, le=100)
    status: VoiceSessionStatus | None = None
    session_type: VoiceSessionType | None = None
