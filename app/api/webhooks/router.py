"""Webhook router aggregating all external service webhooks."""

from fastapi import APIRouter

from app.integrations import load_integrations

webhook_router = APIRouter()

# Load enabled integrations via hook system
load_integrations("webhooks", webhook_router)
