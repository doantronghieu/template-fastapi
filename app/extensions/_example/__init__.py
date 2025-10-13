"""Example extension - template for creating new extensions.

This extension demonstrates the structure and patterns for building modular extensions.
Copy this directory and modify for your specific needs.
"""

from fastapi import APIRouter
from sqladmin import Admin

# Main extension router - aggregates all extension routes
# /EXTENSION_NAME placeholder will be auto-replaced by loader
extension_router = APIRouter(prefix="/EXTENSION_NAME")


def setup_api(app_router: APIRouter) -> None:
    """Register API routes for this extension.

    Args:
        app_router: Main application router to attach extension routes
    """
    from .api.router import router

    # Include extension's internal router
    extension_router.include_router(router)

    # Register extension router with app
    app_router.include_router(extension_router)


def setup_admin(admin: Admin) -> None:
    """Register admin views for this extension.

    Args:
        admin: SQLAdmin instance to register views
    """
    import inspect

    from sqladmin import ModelView

    from .admin import views

    for name, obj in inspect.getmembers(views, inspect.isclass):
        if issubclass(obj, ModelView) and obj is not ModelView:
            admin.add_view(obj)


def setup_tasks() -> None:
    """Import Celery tasks for discovery.

    Tasks are auto-imported via tasks/__init__.py
    """
    from . import tasks  # noqa: F401


def setup_models() -> None:
    """Import models for Alembic discovery.

    Models are auto-imported via models/__init__.py
    """
    from . import models  # noqa: F401
