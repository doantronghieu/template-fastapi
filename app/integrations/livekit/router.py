"""LiveKit API endpoints for token generation and room management."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.integrations.livekit.config import livekit_settings
from app.integrations.livekit.schemas.api import (
    DispatchAgentRequest,
    DispatchAgentResponse,
    ParticipantInfo,
    RoomRequest,
    RoomResponse,
    TokenRequest,
    TokenResponse,
)
from app.integrations.livekit.service import get_room_service, get_token_service

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest) -> TokenResponse:
    """Generate access token for LiveKit room.

    Creates a JWT token that grants the participant access to the
    specified room with the requested permissions.
    """
    service = get_token_service()
    token = service.create_token(
        room_name=request.room_name,
        participant_name=request.participant_name,
        can_publish=request.can_publish,
        can_subscribe=request.can_subscribe,
    )
    return TokenResponse(token=token, url=livekit_settings.LIVEKIT_URL)


@router.post("/rooms", response_model=RoomResponse)
async def create_room(request: RoomRequest) -> RoomResponse:
    """Create a new LiveKit room.

    Creates a room that participants can join using access tokens.
    """
    service = get_room_service()
    room = await service.create_room(
        name=request.name,
        empty_timeout=request.empty_timeout,
        max_participants=request.max_participants,
    )
    return RoomResponse(
        name=room.name,
        sid=room.sid,
        num_participants=room.num_participants,
        creation_time=room.creation_time,
    )


@router.get("/rooms", response_model=list[RoomResponse])
async def list_rooms() -> list[RoomResponse]:
    """List all active LiveKit rooms."""
    service = get_room_service()
    rooms = await service.list_rooms()
    return [
        RoomResponse(
            name=room.name,
            sid=room.sid,
            num_participants=room.num_participants,
            creation_time=room.creation_time,
        )
        for room in rooms
    ]


@router.get("/rooms/{room_name}", response_model=RoomResponse)
async def get_room(room_name: str) -> RoomResponse:
    """Get information about a specific room."""
    service = get_room_service()
    room = await service.get_room(room_name)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomResponse(
        name=room.name,
        sid=room.sid,
        num_participants=room.num_participants,
        creation_time=room.creation_time,
    )


@router.delete("/rooms/{room_name}")
async def delete_room(room_name: str) -> dict:
    """Delete a LiveKit room."""
    service = get_room_service()
    await service.delete_room(room_name)
    return {"status": "deleted"}


@router.get("/rooms/{room_name}/participants", response_model=list[ParticipantInfo])
async def list_participants(room_name: str) -> list[ParticipantInfo]:
    """List participants in a room."""
    service = get_room_service()
    participants = await service.list_participants(room_name)
    return [
        ParticipantInfo(
            identity=p.identity,
            name=p.name,
            state=str(p.state) if p.state else None,
            joined_at=p.joined_at,
        )
        for p in participants
    ]


@router.delete("/rooms/{room_name}/participants/{identity}")
async def remove_participant(room_name: str, identity: str) -> dict:
    """Remove a participant from a room."""
    service = get_room_service()
    await service.remove_participant(room_name, identity)
    return {"status": "removed"}


@router.post("/dispatch", response_model=DispatchAgentResponse)
async def dispatch_agent(request: DispatchAgentRequest) -> DispatchAgentResponse:
    """Dispatch a voice agent to join a room.

    The agent will connect and begin listening for audio.
    """
    service = get_room_service()
    dispatch = await service.dispatch_agent(
        room_name=request.room_name,
        agent_name=request.agent_name,
    )
    return DispatchAgentResponse(
        dispatch_id=dispatch.id,
        room=dispatch.room,
        agent_name=dispatch.agent_name,
    )


@router.get("/test", response_class=HTMLResponse, include_in_schema=False)
async def test_page() -> HTMLResponse:
    """Serve the voice agent test page.

    Access at: /api/integrations/livekit/test
    """
    template = Path(__file__).parent / "test.html"
    content = template.read_text().replace(
        "{{ api_url }}", livekit_settings.BACKEND_URL
    )
    return HTMLResponse(content=content)
