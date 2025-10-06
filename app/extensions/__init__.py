"""Extension loading utility for modular custom features."""

import importlib
import logging
from typing import Literal

from app.core.config import settings

logger = logging.getLogger(__name__)

ExtensionHook = Literal["api", "admin", "tasks", "models"]


def load_extensions(hook: ExtensionHook, *args, **kwargs) -> None:
    """Load enabled extensions for a specific hook.

    Args:
        hook: Extension hook to call (api, admin, tasks, models)
        *args, **kwargs: Passed to extension setup function

    Raises:
        ImportError: In development mode if extension fails to load

    Example:
        >>> from app.extensions import load_extensions
        >>> load_extensions("api", app_router)
    """
    for ext_name in settings.ENABLED_EXTENSIONS:
        try:
            ext_module = importlib.import_module(f"app.extensions.{ext_name}")
            setup_func = getattr(ext_module, f"setup_{hook}", None)

            if setup_func and callable(setup_func):
                setup_func(*args, **kwargs)
                logger.info(f"✓ Loaded extension '{ext_name}' hook '{hook}'")
            else:
                logger.debug(f"Extension '{ext_name}' has no '{hook}' hook")

        except ImportError as e:
            error_msg = f"Extension '{ext_name}' failed to load hook '{hook}': {e}"

            # Fail fast in development (when DATABASE_ECHO=True)
            if settings.DATABASE_ECHO:
                raise ImportError(error_msg) from e
            else:
                logger.warning(error_msg)
