"""SQLAdmin Interface Configuration.

Auto-discovers ModelView classes from app.admin.views, app.features/*/admin, and extensions.
Access at URL/admin (uses sync_engine).

See docs/tech-stack.md for SQLAdmin auto-discovery and template loading details.
See docs/guides/development.md for adding admin views.
"""

import inspect
import logging
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from sqladmin import Admin, ModelView

from app.admin import views
from app.core.autodiscover import ModuleType, autodiscover_admin, get_enabled_modules
from app.core.database import sync_engine

logger = logging.getLogger(__name__)


def setup_admin(app) -> Admin:
    """Configure and setup SQLAlchemy Admin interface."""
    admin = Admin(
        app,
        sync_engine,
        title="FastAPI Admin",
        base_url="/admin",
        templates_dir="app/templates",
    )

    # === Template Loaders ===
    loaders = []

    for ext_name in get_enabled_modules(ModuleType.EXTENSIONS):
        ext_template_dir = Path(f"app/extensions/{ext_name}/resources/templates")
        if ext_template_dir.exists():
            loaders.append(FileSystemLoader(str(ext_template_dir)))

    # Add core templates and SQLAdmin's built-in templates
    loaders.append(FileSystemLoader("app/templates"))
    loaders.append(PackageLoader("sqladmin", "templates"))

    admin.templates.env.loader = ChoiceLoader(loaders)

    # === Core Admin Views ===
    for _, obj in inspect.getmembers(views, inspect.isclass):
        if (
            issubclass(obj, ModelView)
            and obj is not ModelView
            and hasattr(obj, "model")
            and obj.model is not None
        ):
            admin.add_view(obj)

    # === Auto-discovered Admin Views ===
    for module_type in [
        ModuleType.FEATURES,
        ModuleType.INTEGRATIONS,
        ModuleType.EXTENSIONS,
    ]:
        autodiscover_admin(module_type, admin)

    return admin
