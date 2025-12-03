"""LiveKit API request/response schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class LiveKitWebhookEventType(str, Enum):
    """LiveKit webhook event types.

    See: https://docs.livekit.io/home/server/webhooks/#events
    """

    ROOM_STARTED = "room_started"
    ROOM_FINISHED = "room_finished"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    TRACK_PUBLISHED = "track_published"
    TRACK_UNPUBLISHED = "track_unpublished"
    EGRESS_STARTED = "egress_started"
    EGRESS_UPDATED = "egress_updated"
    EGRESS_ENDED = "egress_ended"
    INGRESS_STARTED = "ingress_started"
    INGRESS_ENDED = "ingress_ended"
    SIP_INBOUND_TRUNK_CREATED = "sip_inbound_trunk_created"
    SIP_OUTBOUND_TRUNK_CREATED = "sip_outbound_trunk_created"


class TokenRequest(BaseModel):
    """Request for generating a LiveKit access token."""

    room_name: str = Field(..., description="Name of the room to join")
    participant_name: str = Field(..., description="Identity for the participant")
    can_publish: bool = Field(default=True, description="Allow publishing audio/video")
    can_subscribe: bool = Field(default=True, description="Allow subscribing to others")


class TokenResponse(BaseModel):
    """Response containing the generated access token."""

    token: str = Field(..., description="JWT access token")
    url: str = Field(..., description="LiveKit WebSocket URL")


class RoomRequest(BaseModel):
    """Request for creating a LiveKit room."""

    name: str = Field(..., description="Unique room name")
    empty_timeout: int = Field(
        default=300, description="Seconds before empty room closes"
    )
    max_participants: int = Field(
        default=10, description="Maximum participants allowed"
    )


class RoomResponse(BaseModel):
    """Response containing room information."""

    name: str = Field(..., description="Unique room name")
    sid: str = Field(..., description="Room session identifier")
    num_participants: int = Field(default=0, description="Current participant count")
    creation_time: int | None = Field(
        default=None, description="Room creation timestamp"
    )


class ParticipantInfo(BaseModel):
    """Information about a room participant."""

    identity: str = Field(..., description="Unique participant identity")
    name: str | None = Field(default=None, description="Display name")
    state: str | None = Field(default=None, description="Participant state")
    joined_at: int | None = Field(default=None, description="Join timestamp")


class WebhookEvent(BaseModel):
    """LiveKit webhook event payload."""

    event: str = Field(..., description="Event type (e.g., room_started)")
    room: dict | None = Field(default=None, description="Room information")
    participant: dict | None = Field(
        default=None, description="Participant information"
    )
    track: dict | None = Field(default=None, description="Track information")


class DispatchAgentRequest(BaseModel):
    """Request to dispatch a voice agent to a room."""

    room_name: str = Field(..., description="Room to dispatch agent to")
    agent_name: str = Field(default="", description="Agent name (empty for default)")


class DispatchAgentResponse(BaseModel):
    """Response from agent dispatch."""

    dispatch_id: str = Field(..., description="Dispatch identifier")
    room: str = Field(..., description="Room name")
    agent_name: str = Field(default="", description="Agent name")
