"""LiveKit webhook handlers for room and participant events."""

import logging

from fastapi import APIRouter, Depends, Request
from livekit import api
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.core import get_session
from app.features.voice.services.session_service import VoiceSessionService
from app.integrations.livekit.config import livekit_settings
from app.integrations.livekit.schemas import LiveKitWebhookEventType
from app.integrations.livekit.services import get_webhook_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhooks/events")
async def handle_livekit_webhook(
    request: Request,
    db_session: AsyncSession = Depends(get_session),
) -> dict:
    """Handle LiveKit room/participant events."""
    payload = await request.body()
    auth_header = request.headers.get("Authorization", "")

    try:
        receiver = api.WebhookReceiver(
            livekit_settings.LIVEKIT_API_KEY,
            livekit_settings.LIVEKIT_API_SECRET,
        )
        event = receiver.receive(payload, auth_header)
    except Exception as e:
        logger.warning(f"LiveKit webhook verification failed: {e}")
        return {"status": "error", "message": "Invalid signature"}

    session_service = VoiceSessionService(db_session)
    webhook_service = get_webhook_service()

    event_type = event.event
    room_name = event.room.name if event.room else None

    match event_type:
        case LiveKitWebhookEventType.ROOM_STARTED.value:
            logger.info(f"Room started: {room_name}")
            if room_name:
                await webhook_service.handle_room_started(room_name, session_service)

        case LiveKitWebhookEventType.ROOM_FINISHED.value:
            logger.info(f"Room finished: {room_name}")
            if room_name:
                await webhook_service.handle_room_finished(room_name, session_service)

        case LiveKitWebhookEventType.PARTICIPANT_JOINED.value:
            participant = event.participant
            logger.info(
                f"Participant joined: {participant.identity if participant else 'unknown'} "
                f"in room {room_name}"
            )
            if room_name:
                await webhook_service.handle_participant_joined(
                    room_name, session_service
                )

        case LiveKitWebhookEventType.PARTICIPANT_LEFT.value:
            participant = event.participant
            logger.info(
                f"Participant left: {participant.identity if participant else 'unknown'} "
                f"from room {room_name}"
            )

        case LiveKitWebhookEventType.TRACK_PUBLISHED.value:
            logger.debug(f"Track published in room: {room_name}")

        case LiveKitWebhookEventType.TRACK_UNPUBLISHED.value:
            logger.debug(f"Track unpublished in room: {room_name}")

        case _:
            logger.debug(f"Unhandled LiveKit event: {event_type}")

    return {"status": "ok"}
