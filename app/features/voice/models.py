"""Voice session and message models.

Models for voice conversations.
Supports both web voice chat and phone calls.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, String, Text
from sqlmodel import Field, Relationship

from app.models.base import BaseTable, uuid_fk


class VoiceSessionStatus(str, Enum):
    """Status of a voice session."""

    INITIATED = "initiated"  # Session created, not yet connected
    ACTIVE = "active"  # Session is active/connected
    COMPLETED = "completed"  # Session ended normally
    FAILED = "failed"  # Session failed/errored


class VoiceSessionType(str, Enum):
    """Type of voice session."""

    WEB = "web"
    PHONE_INBOUND = "phone_inbound"
    PHONE_OUTBOUND = "phone_outbound"


class VoiceSession(BaseTable, table=True):
    """Voice conversation session (integration-agnostic).

    Stores session metadata for both web voice chat and phone calls.
    Uses generic fields that work with any provider (LiveKit, Telnyx, etc.).
    """

    __tablename__ = "voice_sessions"

    # Generic identifiers (not provider-specific)
    external_session_id: str = Field(
        index=True,
        unique=True,
        description="External ID (room name, call ID, etc.)",
    )
    provider_type: str = Field(
        sa_column=Column(String(50)),
        description="Provider type (livekit, telnyx, etc.)",
    )

    # Session metadata
    session_type: VoiceSessionType = Field(
        sa_column=Column(String(50)),
        description="Type of session (web, phone_inbound, phone_outbound)",
    )
    status: VoiceSessionStatus = Field(
        default=VoiceSessionStatus.INITIATED,
        sa_column=Column(String(50)),
        description="Current session status",
    )

    # Phone details (for telephony sessions)
    from_number: str | None = Field(
        default=None,
        description="Caller phone number (E.164 format)",
    )
    to_number: str | None = Field(
        default=None,
        description="Called phone number (E.164 format)",
    )

    # Timing (duration can be calculated from started_at and ended_at)
    started_at: datetime | None = Field(
        default=None,
        description="When session became active",
    )
    ended_at: datetime | None = Field(
        default=None,
        description="When session ended",
    )

    # Relationships
    messages: list["VoiceMessage"] = Relationship(back_populates="session")

    @property
    def duration_seconds(self) -> int | None:
        """Calculate duration from started_at and ended_at."""
        if self.started_at and self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return None


class VoiceMessageRole(str, Enum):
    """Role of message sender."""

    USER = "user"
    ASSISTANT = "assistant"


class VoiceMessage(BaseTable, table=True):
    """Individual message in a voice conversation.

    Stores transcribed user speech and AI responses.
    """

    __tablename__ = "voice_messages"

    # Foreign key
    session_id: UUID = uuid_fk("voice_sessions")

    # Message content
    role: VoiceMessageRole = Field(
        sa_column=Column(String(50)),
        description="Message sender role (user or assistant)",
    )
    content: str = Field(
        sa_column=Column(Text),
        description="Message text content",
    )

    # Relationships
    session: VoiceSession = Relationship(back_populates="messages")
