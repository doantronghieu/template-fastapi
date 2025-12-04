"""Library API endpoints auto-discovery.

Auto-discovers and loads API routes from app/lib/*/api.py files.
Each lib module with an api.py file and `router` attribute gets registered.
"""

import importlib
import logging
from pathlib import Path

from fastapi import APIRouter

from app.core.openapi_tags import APITag

logger = logging.getLogger(__name__)

router = APIRouter()


def _load_lib_apis() -> None:
    """Auto-discover and load lib APIs.

    Scans app/lib/*/api.py files and registers routers
    that define a `router` attribute.
    """
    lib_path = Path(__file__).parent.parent.parent / "lib"

    if not lib_path.exists():
        return

    for lib_dir in lib_path.iterdir():
        if not lib_dir.is_dir() or lib_dir.name.startswith("_"):
            continue

        api_file = lib_dir / "api.py"
        if not api_file.exists():
            continue

        module_name = f"app.lib.{lib_dir.name}.api"

        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "router"):
                # Use lib name as tag, capitalize for display
                tag_name = lib_dir.name.upper()
                # Try to get APITag enum if exists, otherwise use string
                tag = getattr(APITag, tag_name, tag_name.replace("_", " ").title())

                router.include_router(
                    module.router,
                    prefix=f"/{lib_dir.name}",
                    tags=[tag],
                )
                logger.debug(f"Loaded lib API: {module_name}")
        except Exception as e:
            logger.warning(f"Failed to load lib API {module_name}: {e}")


# Auto-load lib APIs on module import
_load_lib_apis()
