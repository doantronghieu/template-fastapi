"""Telnyx integration for telephony (PSTN, SIP, call control).

Implements TelephonyProvider interface using Telnyx SDK.
"""

from fastapi import APIRouter


def setup_api(router: APIRouter) -> None:
    """Register Telnyx API routes."""
    from app.integrations.telnyx.api import router as telnyx_router

    router.include_router(telnyx_router, prefix="/telnyx", tags=["Telnyx"])


def setup_webhooks(router: APIRouter) -> None:
    """Register Telnyx webhook routes."""
    from app.integrations.telnyx.webhooks import router as webhook_router

    router.include_router(webhook_router, prefix="/telnyx", tags=["Telnyx Webhooks"])
