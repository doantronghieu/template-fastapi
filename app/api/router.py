"""API Router."""

from fastapi import APIRouter

from app.api import examples, health, tasks
from app.core.autodiscover import (
    ModuleType,
    autodiscover_routers,
    autodiscover_webhooks,
)

api_router = APIRouter()

# === Core Routes ===
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(examples.router, tags=["Examples"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])

# === Auto-discovered Routes ===
ROUTER_CONFIG = {
    ModuleType.FEATURES: {
        "prefix_template": "/features/{name}",
        "include_in_schema": False,
    },
    ModuleType.LIB: {"prefix_template": "/lib/{name}"},
    ModuleType.INTEGRATIONS: {"prefix_template": "/integrations/{name}"},
    ModuleType.EXTENSIONS: {"prefix_template": "/extensions/{name}"},
}

for module_type, config in ROUTER_CONFIG.items():
    autodiscover_routers(module_type, api_router, **config)

# === Webhook Router ===
webhook_router = APIRouter()

for module_type in [
    ModuleType.FEATURES,
    ModuleType.INTEGRATIONS,
    ModuleType.EXTENSIONS,
]:
    autodiscover_webhooks(module_type, webhook_router)

api_router.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
