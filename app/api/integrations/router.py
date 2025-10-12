"""Integration router aggregating all external service integration endpoints."""

from fastapi import APIRouter

from . import messenger

integration_router = APIRouter()

# Register integration endpoints
integration_router.include_router(messenger.router, prefix="/messenger")
