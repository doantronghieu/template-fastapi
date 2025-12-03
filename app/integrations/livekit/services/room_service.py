"""LiveKit room service for managing rooms."""

import logging
from functools import lru_cache
from typing import Annotated

from livekit import api

from app.integrations.livekit.client import get_livekit_client
from app.integrations.livekit.config import livekit_settings

logger = logging.getLogger(__name__)


class RoomService:
    """Manage LiveKit rooms.

    Provides CRUD operations for LiveKit rooms and utilities
    for SIP integration.
    """

    def __init__(
        self,
        client: Annotated[api.LiveKitAPI | None, "LiveKitAPI instance"] = None,
    ) -> None:
        """Initialize with LiveKit API client."""
        self.client = client or get_livekit_client()

    async def create_room(
        self,
        name: Annotated[str, "Unique room name"],
        empty_timeout: Annotated[int, "Seconds before empty room closes"] = 300,
        max_participants: Annotated[int, "Maximum participants allowed"] = 10,
    ) -> api.Room:
        """Create a new room."""
        return await self.client.room.create_room(
            api.CreateRoomRequest(
                name=name,
                empty_timeout=empty_timeout,
                max_participants=max_participants,
            )
        )

    async def list_rooms(self) -> list[api.Room]:
        """List all active rooms."""
        response = await self.client.room.list_rooms(api.ListRoomsRequest())
        return list(response.rooms)

    async def get_room(
        self,
        name: Annotated[str, "Room name to look up"],
    ) -> api.Room | None:
        """Get room by name. Returns None if not found."""
        rooms = await self.list_rooms()
        for room in rooms:
            if room.name == name:
                return room
        return None

    async def delete_room(
        self,
        name: Annotated[str, "Room name to delete"],
    ) -> None:
        """Delete a room."""
        await self.client.room.delete_room(api.DeleteRoomRequest(room=name))

    async def list_participants(
        self,
        room_name: Annotated[str, "Room to query"],
    ) -> list[api.ParticipantInfo]:
        """List participants in a room."""
        response = await self.client.room.list_participants(
            api.ListParticipantsRequest(room=room_name)
        )
        return list(response.participants)

    async def remove_participant(
        self,
        room_name: Annotated[str, "Room name"],
        identity: Annotated[str, "Participant identity to remove"],
    ) -> None:
        """Remove participant from room."""
        await self.client.room.remove_participant(
            api.RoomParticipantIdentity(room=room_name, identity=identity)
        )

    def get_sip_uri(
        self,
        room_name: Annotated[str, "Target room name"],
    ) -> str:
        """Get SIP URI for transferring calls to room (sip:room@host)."""
        return livekit_settings.get_sip_uri(room_name)

    async def cleanup_room(
        self,
        room_name: Annotated[str, "Room name to clean up"],
    ) -> bool:
        """Clean up room after session ends. Returns True if deleted."""
        try:
            await self.delete_room(room_name)
            logger.info(f"Deleted LiveKit room: {room_name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete room {room_name}: {e}")
            return False

    async def dispatch_agent(
        self,
        room_name: Annotated[str, "Room to dispatch agent to"],
        agent_name: Annotated[str, "Agent name (empty for default)"] = "",
    ) -> api.AgentDispatch:
        """Dispatch a voice agent to join the room."""
        dispatch = await self.client.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name=agent_name,
            )
        )
        logger.info(f"Dispatched agent to room: {room_name}")
        return dispatch

    async def list_agent_dispatches(
        self,
        room_name: Annotated[str, "Room to query"],
    ) -> list[api.AgentDispatch]:
        """List active agent dispatches in a room."""
        return await self.client.agent_dispatch.list_dispatch(room_name=room_name)


@lru_cache(maxsize=1)
def get_room_service() -> RoomService:
    """Cached singleton."""
    return RoomService()
