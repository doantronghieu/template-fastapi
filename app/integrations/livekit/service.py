"""LiveKit services for room, token, and webhook management."""

import logging
from datetime import timedelta
from functools import lru_cache
from typing import Annotated

from livekit import api

from app.features.voice.models import VoiceSessionStatus, VoiceSessionType
from app.features.voice.service import VoiceSessionService
from app.integrations.livekit.client import get_livekit_client
from app.integrations.livekit.config import livekit_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Room Service
# =============================================================================


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


# =============================================================================
# Token Service
# =============================================================================


class TokenService:
    """Generate LiveKit access tokens for participants.

    Tokens are JWTs signed with the API secret that grant
    specific permissions for room access.
    """

    def create_token(
        self,
        room_name: Annotated[str, "Name of the room to join"],
        participant_name: Annotated[str, "Identity for the participant"],
        can_publish: Annotated[bool, "Allow publishing audio/video"] = True,
        can_subscribe: Annotated[bool, "Allow subscribing to others"] = True,
        is_agent: Annotated[bool, "Mark as agent participant (server-side)"] = False,
        ttl_seconds: Annotated[int, "Token validity duration in seconds"] = 3600,
    ) -> str:
        """Generate JWT access token for room."""
        token = api.AccessToken(
            livekit_settings.LIVEKIT_API_KEY,
            livekit_settings.LIVEKIT_API_SECRET,
        )

        # Set identity and display name
        token.with_identity(participant_name)
        token.with_name(participant_name)
        token.with_ttl(timedelta(seconds=ttl_seconds))

        # Configure grants
        grants = api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=can_publish,
            can_subscribe=can_subscribe,
        )

        if is_agent:
            grants.agent = True

        token.with_grants(grants)

        return token.to_jwt()


@lru_cache(maxsize=1)
def get_token_service() -> TokenService:
    """Cached singleton."""
    return TokenService()


# =============================================================================
# Webhook Service
# =============================================================================


class WebhookService:
    """Handle LiveKit webhook events.

    Manages voice session lifecycle based on room events.
    """

    async def handle_room_started(
        self,
        room_name: Annotated[str, "LiveKit room name"],
        session_service: VoiceSessionService,
    ) -> None:
        """Handle room_started webhook - create voice session."""
        try:
            await session_service.create_session(
                session_type=VoiceSessionType.WEB,
                provider_type="livekit",
                external_session_id=room_name,
            )
            logger.info(f"Created voice session for room: {room_name}")
        except Exception as e:
            logger.error(f"Failed to create session for room {room_name}: {e}")

    async def handle_room_finished(
        self,
        room_name: Annotated[str, "LiveKit room name"],
        session_service: VoiceSessionService,
    ) -> None:
        """Handle room_finished webhook - complete session."""
        try:
            session = await session_service.get_session_by_external_id(room_name)
            if session:
                await session_service.update_status(
                    session.id, VoiceSessionStatus.COMPLETED
                )
                logger.info(f"Updated session status to completed: {room_name}")
        except Exception as e:
            logger.error(f"Failed to update session for room {room_name}: {e}")

    async def handle_participant_joined(
        self,
        room_name: Annotated[str, "LiveKit room name"],
        session_service: VoiceSessionService,
    ) -> None:
        """Handle participant_joined webhook - activate session."""
        try:
            session = await session_service.get_session_by_external_id(room_name)
            if session and session.status == VoiceSessionStatus.INITIATED:
                await session_service.update_status(
                    session.id, VoiceSessionStatus.ACTIVE
                )
                logger.info(f"Updated session status to active: {room_name}")
        except Exception as e:
            logger.error(f"Failed to update session for room {room_name}: {e}")


@lru_cache(maxsize=1)
def get_webhook_service() -> WebhookService:
    """Cached singleton."""
    return WebhookService()


__all__ = [
    "RoomService",
    "get_room_service",
    "TokenService",
    "get_token_service",
    "WebhookService",
    "get_webhook_service",
]
