"""LiveKit integration for real-time voice/video communication.

Provides room management, token generation, and webhook handling.
"""

from fastapi import APIRouter


def setup_api(router: APIRouter) -> None:
    """Register LiveKit API routes."""
    from app.integrations.livekit.api import router as livekit_router

    router.include_router(livekit_router, prefix="/livekit", tags=["LiveKit"])


def setup_webhooks(router: APIRouter) -> None:
    """Register LiveKit webhook routes."""
    from app.integrations.livekit.webhooks import router as webhook_router

    router.include_router(webhook_router, prefix="/livekit", tags=["LiveKit Webhooks"])
