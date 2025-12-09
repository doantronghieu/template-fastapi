"""Telephony provider schemas.

Common data structures used across telephony providers.
"""

from enum import Enum

from pydantic import BaseModel, Field


class CallDirection(str, Enum):
    """Direction of a phone call."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallStatus(str, Enum):
    """Status of a phone call."""

    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    TRANSFERRED = "transferred"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"


class CallResult(BaseModel):
    """Result from initiating or querying a call."""

    call_id: str = Field(..., description="Provider-specific call identifier")
    status: CallStatus = Field(..., description="Current call status")
    direction: CallDirection | None = Field(
        default=None, description="Call direction (inbound/outbound)"
    )
    from_number: str | None = Field(
        default=None, description="Caller phone number (E.164 format)"
    )
    to_number: str | None = Field(
        default=None, description="Called phone number (E.164 format)"
    )
    duration_seconds: int | None = Field(
        default=None, description="Call duration in seconds"
    )
