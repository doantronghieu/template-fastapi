from fastapi import APIRouter

from app.api import examples, health, lib, messaging, tasks
from app.core.openapi_tags import APITag
from app.extensions import load_extensions

api_router = APIRouter()

# Core API routes
api_router.include_router(health.router, tags=[APITag.HEALTH])
api_router.include_router(examples.router, tags=[APITag.EXAMPLES])
api_router.include_router(messaging.router, tags=[APITag.MESSAGING])
api_router.include_router(tasks.router, prefix="/tasks", tags=[APITag.TASKS])
api_router.include_router(lib.router, prefix="/lib")

# Load extension API routes
load_extensions("api", api_router)
