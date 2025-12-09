"""Telnyx-specific schemas for API and webhooks."""

from enum import Enum

from pydantic import BaseModel, Field


class TelnyxCallEventType(str, Enum):
    """Telnyx call event types."""

    CALL_INITIATED = "call.initiated"
    CALL_ANSWERED = "call.answered"
    CALL_BRIDGED = "call.bridged"
    CALL_HANGUP = "call.hangup"
    CALL_MACHINE_DETECTION_ENDED = "call.machine.detection.ended"
    CALL_SPEAK_STARTED = "call.speak.started"
    CALL_SPEAK_ENDED = "call.speak.ended"


class CallActionStatus(str, Enum):
    """Call action response status values."""

    INITIATED = "initiated"
    ANSWERED = "answered"
    HANGUP = "hangup"
    TRANSFERRED = "transferred"


class TelnyxWebhookData(BaseModel):
    """Data payload in Telnyx webhook event."""

    event_type: str = Field(..., description="Telnyx event type (e.g., call.initiated)")
    call_control_id: str = Field(..., description="Unique call control identifier")
    call_leg_id: str | None = Field(default=None, description="Call leg identifier")
    call_session_id: str | None = Field(
        default=None, description="Call session identifier"
    )
    client_state: str | None = Field(default=None, description="Custom client state")
    from_: str | None = Field(default=None, alias="from", description="Caller number")
    to: str | None = Field(default=None, description="Called number")
    direction: str | None = Field(default=None, description="Call direction")
    state: str | None = Field(default=None, description="Call state")


class TelnyxWebhookEvent(BaseModel):
    """Telnyx webhook event structure."""

    data: TelnyxWebhookData = Field(..., description="Event data payload")
    meta: dict | None = Field(default=None, description="Event metadata")


class InitiateCallRequest(BaseModel):
    """Request to initiate an outbound call."""

    to_number: str = Field(..., description="Destination phone number (E.164)")
    from_number: str | None = Field(default=None, description="Caller ID (E.164)")
    webhook_url: str | None = Field(default=None, description="Custom webhook URL")


class InitiateCallResponse(BaseModel):
    """Response from initiating a call."""

    call_control_id: str = Field(..., description="Telnyx call control ID")
    status: str = Field(default="initiated", description="Initial call status")
