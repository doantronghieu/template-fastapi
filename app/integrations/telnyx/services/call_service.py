"""Telnyx call service for handling call operations."""

import logging
from functools import lru_cache
from typing import Annotated

from telnyx import AsyncTelnyx

from app.features.voice.models import VoiceSessionStatus, VoiceSessionType
from app.features.voice.services.session_service import VoiceSessionService
from app.integrations.livekit.config import livekit_settings
from app.integrations.livekit.services import get_room_service
from app.integrations.telnyx.client import get_telnyx_client
from app.integrations.telnyx.schemas import TelnyxWebhookData

logger = logging.getLogger(__name__)


class CallService:
    """Manage Telnyx call operations and webhook events.

    Handles call lifecycle events and integrates with
    LiveKit for voice sessions.
    """

    def __init__(
        self,
        client: Annotated[AsyncTelnyx | None, "Telnyx async client"] = None,
    ) -> None:
        """Initialize with Telnyx client."""
        self.client = client or get_telnyx_client()

    async def handle_call_initiated(
        self,
        call_control_id: Annotated[str, "Telnyx call control ID"],
        data: TelnyxWebhookData,
        session_service: VoiceSessionService,
    ) -> None:
        """Handle call.initiated event - process inbound calls.

        For inbound calls: creates voice session, LiveKit room,
        answers call, and transfers to SIP endpoint.
        """
        direction = data.direction
        logger.info(
            f"Call initiated: {call_control_id} "
            f"direction={direction} from={data.from_} to={data.to}"
        )

        if direction == "inbound":
            await self._handle_inbound_call(call_control_id, data, session_service)

    async def handle_call_answered(
        self,
        call_control_id: Annotated[str, "Telnyx call control ID"],
        session_service: VoiceSessionService,
    ) -> None:
        """Handle call.answered event - activate session."""
        logger.info(f"Call answered: {call_control_id}")
        try:
            session = await session_service.update_status_by_external_id(
                call_control_id, VoiceSessionStatus.ACTIVE
            )
            if session:
                logger.info(f"Updated session status to active: {call_control_id}")
        except Exception as e:
            logger.error(f"Failed to update session for call {call_control_id}: {e}")

    async def handle_call_hangup(
        self,
        call_control_id: Annotated[str, "Telnyx call control ID"],
        session_service: VoiceSessionService,
    ) -> None:
        """Handle call.hangup event - complete session and cleanup."""
        logger.info(f"Call hangup: {call_control_id}")
        try:
            session = await session_service.update_status_by_external_id(
                call_control_id, VoiceSessionStatus.COMPLETED
            )
            if session:
                logger.info(f"Updated session status to completed: {call_control_id}")

            # Clean up LiveKit room
            room_name = f"call-{call_control_id[:12]}"
            room_service = get_room_service()
            await room_service.cleanup_room(room_name)

        except Exception as e:
            logger.error(f"Failed to update session for call {call_control_id}: {e}")

    async def _handle_inbound_call(
        self,
        call_control_id: str,
        data: TelnyxWebhookData,
        session_service: VoiceSessionService,
    ) -> None:
        """Handle incoming phone call by transferring to LiveKit."""
        try:
            # Create voice session
            await session_service.create_session(
                session_type=VoiceSessionType.PHONE_INBOUND,
                provider_type="telnyx",
                external_session_id=call_control_id,
                from_number=data.from_,
                to_number=data.to,
            )
            logger.info(f"Created voice session for call: {call_control_id}")

            # Create LiveKit room and get SIP URI
            room_service = get_room_service()
            room_name = f"call-{call_control_id[:12]}"
            await room_service.create_room(room_name)
            sip_uri = livekit_settings.get_sip_uri(room_name)

            # Answer and transfer to LiveKit
            await self.client.calls.actions.answer(call_control_id)
            await self.client.calls.actions.transfer(call_control_id, to=sip_uri)
            logger.info(f"Transferred inbound call {call_control_id} to {sip_uri}")

        except Exception as e:
            logger.error(f"Failed to handle inbound call {call_control_id}: {e}")
            await self._handle_call_failure(call_control_id, session_service)

    async def _handle_call_failure(
        self,
        call_control_id: str,
        session_service: VoiceSessionService,
    ) -> None:
        """Handle call failure - update status and hangup."""
        try:
            await session_service.update_status_by_external_id(
                call_control_id, VoiceSessionStatus.FAILED
            )
        except Exception:
            pass

        try:
            await self.client.calls.actions.hangup(call_control_id)
        except Exception:
            pass


@lru_cache(maxsize=1)
def get_call_service() -> CallService:
    """Cached singleton."""
    return CallService()
