"""SQLAdmin Interface Configuration.

Auto-discovers ModelView classes from app.admin.views and extension modules.
Access at http://127.0.0.1:8000/admin (uses sync_engine).

See docs/tech-stack.md for SQLAdmin auto-discovery and template loading details.
See docs/guides/development.md for adding admin views.
"""

import inspect
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from sqladmin import Admin, ModelView

from app.admin import views
from app.core.config import settings
from app.core.database import sync_engine
from app.extensions import load_extensions


def setup_admin(app) -> Admin:
    """Configure and setup SQLAlchemy Admin interface."""
    admin = Admin(
        app,
        sync_engine,
        title="FastAPI Admin",
        base_url="/admin",
        templates_dir="app/templates",
    )

    # Configure Jinja2 to search extension templates before falling back to SQLAdmin defaults
    # This allows extensions to override templates while keeping core clean
    loaders = []

    # Add extension template directories dynamically
    for ext_name in settings.ENABLED_EXTENSIONS:
        ext_template_dir = Path(f"app/extensions/{ext_name}/templates")
        if ext_template_dir.exists():
            loaders.append(FileSystemLoader(str(ext_template_dir)))

    # Add core templates and SQLAdmin's built-in templates
    loaders.append(FileSystemLoader("app/templates"))
    loaders.append(PackageLoader("sqladmin", "templates"))

    admin.templates.env.loader = ChoiceLoader(loaders)

    # Auto-register all ModelView subclasses from app.admin.views (core)
    for name, obj in inspect.getmembers(views, inspect.isclass):
        if (
            issubclass(obj, ModelView)
            and obj is not ModelView
            and hasattr(obj, "model")
            and obj.model is not None
        ):
            admin.add_view(obj)

    # Load extension admin views
    load_extensions("admin", admin)

    return admin
