"""Integration router aggregating all external service integration endpoints."""

from fastapi import APIRouter

from app.integrations import load_integrations

integration_router = APIRouter()

# Load enabled integrations via hook system
load_integrations("api", integration_router)
