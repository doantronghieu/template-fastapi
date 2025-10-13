"""Integration router aggregating all external service integration endpoints."""

from fastapi import APIRouter

from app.core.openapi_tags import APITag

from . import gmail, messenger

integration_router = APIRouter()

# Register integration endpoints with specific tags
integration_router.include_router(
    messenger.router, prefix="/messenger", tags=[APITag.MESSENGER]
)
integration_router.include_router(gmail.router, prefix="/gmail", tags=[APITag.GMAIL])
