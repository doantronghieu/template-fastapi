"""Telnyx telephony provider implementation."""

from functools import lru_cache
from typing import Annotated

from telnyx import AsyncTelnyx

from app.integrations.telnyx.client import get_telnyx_client
from app.integrations.telnyx.config import telnyx_settings
from app.lib.telephony.base import TelephonyProvider


class TelnyxTelephonyProvider(TelephonyProvider):
    """Telnyx implementation of TelephonyProvider.

    Provides call control for inbound and outbound calls.
    """

    def __init__(
        self,
        client: Annotated[AsyncTelnyx | None, "Telnyx async client"] = None,
    ) -> None:
        """Initialize provider with Telnyx client."""
        self.client = client or get_telnyx_client()

    async def initiate_call(
        self,
        to_number: Annotated[str, "Destination phone number (E.164 format)"],
        from_number: Annotated[str, "Caller ID phone number (E.164 format)"],
        webhook_url: Annotated[str, "URL to receive call events"],
    ) -> str:
        """Initiate an outbound call. Returns call control ID."""
        response = await self.client.calls.dial(
            connection_id=telnyx_settings.TELNYX_SIP_TRUNK_ID,
            to=to_number,
            from_=from_number or telnyx_settings.TELNYX_PHONE_NUMBER,
            webhook_url=webhook_url,
        )
        return response.data.call_control_id

    async def answer_call(
        self,
        call_id: Annotated[str, "Call control ID from Telnyx"],
    ) -> None:
        """Answer an incoming call."""
        await self.client.calls.actions.answer(call_id)

    async def hangup_call(
        self,
        call_id: Annotated[str, "Call control ID from Telnyx"],
    ) -> None:
        """End an active call."""
        await self.client.calls.actions.hangup(call_id)

    async def transfer_to_sip(
        self,
        call_id: Annotated[str, "Call control ID from Telnyx"],
        sip_uri: Annotated[str, "SIP URI (e.g., sip:room@livekit.cloud)"],
    ) -> None:
        """Transfer call to a SIP endpoint (e.g., LiveKit)."""
        await self.client.calls.actions.transfer(call_id, to=sip_uri)


@lru_cache(maxsize=1)
def get_telephony_provider() -> TelnyxTelephonyProvider:
    """Cached singleton."""
    return TelnyxTelephonyProvider()
