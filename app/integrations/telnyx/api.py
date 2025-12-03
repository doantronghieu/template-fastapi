"""Telnyx API endpoints for call management."""

from fastapi import APIRouter, HTTPException

from app.integrations.telnyx.config import telnyx_settings
from app.integrations.telnyx.provider import get_telephony_provider
from app.integrations.telnyx.schemas import (
    CallActionStatus,
    InitiateCallRequest,
    InitiateCallResponse,
)

router = APIRouter()


@router.post("/calls", response_model=InitiateCallResponse)
async def initiate_call(request: InitiateCallRequest) -> InitiateCallResponse:
    """Initiate an outbound phone call."""
    if not telnyx_settings.TELNYX_SIP_TRUNK_ID:
        raise HTTPException(
            status_code=503,
            detail="Telnyx SIP trunk not configured",
        )

    provider = get_telephony_provider()
    webhook_url = request.webhook_url or ""

    call_control_id = await provider.initiate_call(
        to_number=request.to_number,
        from_number=request.from_number or telnyx_settings.TELNYX_PHONE_NUMBER,
        webhook_url=webhook_url,
    )

    return InitiateCallResponse(
        call_control_id=call_control_id,
        status="initiated",
    )


@router.post("/calls/{call_control_id}/answer")
async def answer_call(call_control_id: str) -> dict:
    """Answer an incoming call."""
    provider = get_telephony_provider()
    await provider.answer_call(call_control_id)
    return {"status": CallActionStatus.ANSWERED.value}


@router.post("/calls/{call_control_id}/hangup")
async def hangup_call(call_control_id: str) -> dict:
    """Hang up an active call."""
    provider = get_telephony_provider()
    await provider.hangup_call(call_control_id)
    return {"status": CallActionStatus.HANGUP.value}


@router.post("/calls/{call_control_id}/transfer")
async def transfer_call(call_control_id: str, sip_uri: str) -> dict:
    """Transfer a call to a SIP endpoint."""
    provider = get_telephony_provider()
    await provider.transfer_to_sip(call_control_id, sip_uri)
    return {"status": CallActionStatus.TRANSFERRED.value}
