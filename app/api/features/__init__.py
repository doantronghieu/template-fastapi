"""Features API router.

Auto-discovers and loads feature APIs from app/features/*/api.py or app/features/*/api/__init__.py.
Mounted at /api/features/{feature_name}/*.
"""

import importlib
import logging
from pathlib import Path

from fastapi import APIRouter

logger = logging.getLogger(__name__)

features_router = APIRouter()


def _load_feature_apis() -> None:
    """Auto-discover and load feature APIs.

    Scans app/features/*/ for api.py or api/__init__.py and registers routers
    that define a `router` attribute.
    """
    features_path = Path(__file__).parent.parent.parent / "features"

    if not features_path.exists():
        return

    for feature_dir in features_path.iterdir():
        if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
            continue

        # Check for api package first (api/__init__.py), then single file (api.py)
        api_package = feature_dir / "api" / "__init__.py"
        api_file = feature_dir / "api.py"

        if not api_package.exists() and not api_file.exists():
            continue

        module_name = f"app.features.{feature_dir.name}.api"

        # Convert underscore to hyphen for URL prefix
        url_prefix = f"/{feature_dir.name.replace('_', '-')}"

        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "router"):
                # Generate tag from directory name
                tag = feature_dir.name.replace("_", " ").title()
                features_router.include_router(
                    module.router,
                    prefix=url_prefix,
                    tags=[tag],
                )
                logger.debug(f"Loaded feature API: {module_name}")
        except Exception as e:
            logger.warning(f"Failed to load feature API {module_name}: {e}")


# Auto-load feature APIs on module import
_load_feature_apis()
