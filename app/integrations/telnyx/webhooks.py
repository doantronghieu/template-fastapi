"""Telnyx webhook handlers for call events."""

import logging

from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.core import get_session
from app.features.voice.service import VoiceSessionService
from app.integrations.telnyx.schemas.api import TelnyxCallEventType, TelnyxWebhookEvent
from app.integrations.telnyx.service import get_call_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhooks/calls")
async def handle_call_webhook(
    request: Request,
    db_session: AsyncSession = Depends(get_session),
) -> dict:
    """Handle Telnyx call events."""
    payload = await request.json()

    try:
        event = TelnyxWebhookEvent(**payload)
    except Exception as e:
        logger.warning(f"Failed to parse Telnyx webhook: {e}")
        return {"status": "error", "message": "Invalid payload"}

    session_service = VoiceSessionService(db_session)
    call_service = get_call_service()

    event_type = event.data.event_type
    call_control_id = event.data.call_control_id

    match event_type:
        case TelnyxCallEventType.CALL_INITIATED.value:
            await call_service.handle_call_initiated(
                call_control_id, event.data, session_service
            )

        case TelnyxCallEventType.CALL_ANSWERED.value:
            await call_service.handle_call_answered(call_control_id, session_service)

        case TelnyxCallEventType.CALL_HANGUP.value:
            await call_service.handle_call_hangup(call_control_id, session_service)

        case _:
            logger.debug(f"Unhandled Telnyx event: {event_type}")

    return {"status": "ok"}
