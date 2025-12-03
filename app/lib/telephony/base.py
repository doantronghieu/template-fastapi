"""Base protocol for telephony provider implementations.

Defines the common interface that all telephony providers must implement,
enabling runtime provider switching via the Strategy pattern.
"""

from typing import Annotated, Protocol


class TelephonyProvider(Protocol):
    """Protocol defining the interface for telephony provider implementations.

    All telephony provider implementations must support:
    - Initiating outbound calls
    - Answering incoming calls
    - Hanging up calls
    - Transferring calls to SIP endpoints
    """

    async def initiate_call(
        self,
        to_number: Annotated[str, "Destination phone number (E.164 format)"],
        from_number: Annotated[str, "Caller ID phone number (E.164 format)"],
        webhook_url: Annotated[str, "URL to receive call events"],
    ) -> str:
        """Initiate an outbound call. Returns external call ID from provider."""
        ...

    async def answer_call(
        self,
        call_id: Annotated[str, "External call ID from the provider"],
    ) -> None:
        """Answer an incoming call."""
        ...

    async def hangup_call(
        self,
        call_id: Annotated[str, "External call ID from the provider"],
    ) -> None:
        """End an active call."""
        ...

    async def transfer_to_sip(
        self,
        call_id: Annotated[str, "External call ID from the provider"],
        sip_uri: Annotated[str, "SIP URI (e.g., sip:room@livekit.cloud)"],
    ) -> None:
        """Transfer call to a SIP endpoint."""
        ...
