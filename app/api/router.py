from fastapi import APIRouter

from app.api import examples, health, tasks

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(examples.router, tags=["examples"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
