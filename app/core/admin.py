import inspect

from sqladmin import Admin, ModelView

from app.admin import views
from app.core.database import sync_engine
from app.extensions import load_extensions


def setup_admin(app) -> Admin:
    """Configure and setup SQLAlchemy Admin interface."""
    admin = Admin(
        app,
        sync_engine,
        title="FastAPI Admin",
        base_url="/admin",
    )

    # Auto-register all ModelView subclasses from app.admin.views (core)
    for name, obj in inspect.getmembers(views, inspect.isclass):
        if issubclass(obj, ModelView) and obj is not ModelView:
            admin.add_view(obj)

    # Load extension admin views
    load_extensions("admin", admin)

    return admin
