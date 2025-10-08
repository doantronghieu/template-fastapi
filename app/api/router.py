from fastapi import APIRouter

from app.api import examples, health, lib, messaging, tasks
from app.extensions import load_extensions

api_router = APIRouter()

# Core API routes
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(examples.router, tags=["Examples"])
api_router.include_router(messaging.router, tags=["Messaging"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(lib.router, prefix="/lib")

# Load extension API routes
load_extensions("api", api_router)
