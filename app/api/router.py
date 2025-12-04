from fastapi import APIRouter

from app.api import examples, health, lib, messaging, tasks, users
from app.api.features import features_router
from app.api.integrations.router import integration_router
from app.api.webhooks.router import webhook_router
from app.core.openapi_tags import APITag
from app.extensions import load_extensions

api_router = APIRouter()

# Core API routes
api_router.include_router(health.router, tags=[APITag.HEALTH])
api_router.include_router(examples.router, tags=[APITag.EXAMPLES])
api_router.include_router(messaging.router, tags=[APITag.MESSAGING])
api_router.include_router(tasks.router, prefix="/tasks", tags=[APITag.TASKS])
api_router.include_router(users.router, prefix="/users", tags=[APITag.USERS])
api_router.include_router(lib.router, prefix="/lib")

# Integration routes (tags applied at integration router level)
api_router.include_router(integration_router, prefix="/integrations")

# Feature routes (internal, not in OpenAPI schema)
api_router.include_router(features_router, prefix="/features", include_in_schema=False)

# Webhook routes
api_router.include_router(webhook_router, prefix="/webhooks", tags=[APITag.WEBHOOKS])

# Load extension API routes
load_extensions("api", api_router)
