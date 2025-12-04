"""SQLAdmin Interface Configuration.

Auto-discovers ModelView classes from app.admin.views, app.features/*/admin, and extensions.
Access at http://127.0.0.1:8000/admin (uses sync_engine).

See docs/tech-stack.md for SQLAdmin auto-discovery and template loading details.
See docs/guides/development.md for adding admin views.
"""

import importlib
import inspect
import logging
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from sqladmin import Admin, ModelView

from app.admin import views
from app.core.config import settings
from app.core.database import sync_engine
from app.extensions import load_extensions

logger = logging.getLogger(__name__)


def _load_feature_admin_views(admin: Admin) -> None:
    """Auto-discover and register admin views from features.

    Scans app/features/*/admin/ for ModelView subclasses.
    """
    features_path = Path(__file__).parent.parent / "features"

    if not features_path.exists():
        return

    for feature_dir in features_path.iterdir():
        if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
            continue

        admin_package = feature_dir / "admin" / "__init__.py"
        admin_file = feature_dir / "admin.py"

        if not admin_package.exists() and not admin_file.exists():
            continue

        module_name = f"app.features.{feature_dir.name}.admin"

        try:
            module = importlib.import_module(module_name)

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, ModelView)
                    and obj is not ModelView
                    and hasattr(obj, "model")
                    and obj.model is not None
                ):
                    admin.add_view(obj)
                    logger.debug(f"Loaded feature admin view: {name}")

        except Exception as e:
            logger.warning(f"Failed to load feature admin {module_name}: {e}")


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

    # Load feature admin views
    _load_feature_admin_views(admin)

    # Load extension admin views
    load_extensions("admin", admin)

    return admin
