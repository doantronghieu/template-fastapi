"""Webhook router aggregating all external service webhooks."""

from fastapi import APIRouter

from . import messenger

webhook_router = APIRouter()

# Register webhook endpoints
webhook_router.include_router(messenger.router, prefix="/messenger")
