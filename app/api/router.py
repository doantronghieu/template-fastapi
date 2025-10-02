from fastapi import APIRouter

from app.api import examples, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(examples.router, tags=["examples"])
