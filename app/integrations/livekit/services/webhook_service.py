"""LiveKit webhook service for room and participant events."""

import logging
from functools import lru_cache
from typing import Annotated

from app.features.voice.models import VoiceSessionStatus, VoiceSessionType
from app.features.voice.services.session_service import VoiceSessionService

logger = logging.getLogger(__name__)


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
