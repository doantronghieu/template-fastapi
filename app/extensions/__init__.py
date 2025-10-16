"""Extension loading utility for modular custom features."""

import importlib
import logging
from pathlib import Path
from typing import Literal

from app.core.config import settings

logger = logging.getLogger(__name__)

ExtensionHook = Literal["api", "admin", "tasks", "models", "message_handlers"]


def get_extension_env_path(config_file_path: str) -> str:
    """Get extension .env file path without generating it.

    Pattern: .env.[extension_folder_name]
    Example: app/extensions/_example -> .env._example

    Args:
        config_file_path: Pass __file__ from the config.py module

    Returns:
        Path to the .env file in project root
    """
    # Get extension folder name from config file path
    extension_folder = Path(config_file_path).parent.name

    # Project root (3 levels up: config.py -> extension -> extensions -> app -> root)
    project_root = Path(config_file_path).parent.parent.parent.parent

    # .env file path
    env_file = project_root / f".env.{extension_folder}"

    return str(env_file)


def generate_extension_env(config_file_path: str, settings_class: type) -> None:
    """Generate .env file for extension if it doesn't exist.

    Introspects Settings class fields to create template.

    Args:
        config_file_path: Pass __file__ from the config.py module
        settings_class: Your Settings class

    Example:
        >>> # In app/extensions/my_extension/config.py
        >>> class MySettings(BaseSettings):
        ...     API_KEY: str = Field(default="", description="API key")
        >>> generate_extension_env(__file__, MySettings)
    """
    # Get extension folder name
    extension_folder = Path(config_file_path).parent.name

    # Get .env file path
    env_file = Path(get_extension_env_path(config_file_path))

    # Auto-generate if doesn't exist
    if not env_file.exists():
        lines = [f"# {extension_folder.upper()} Extension Configuration", ""]

        # Introspect Settings class fields
        if hasattr(settings_class, "model_fields"):
            for field_name, field_info in settings_class.model_fields.items():
                # Get description from Field
                description = (
                    field_info.description if field_info.description else field_name
                )
                lines.append(f"# {description}")
                lines.append(f"{field_name}=")
                lines.append("")

        env_file.write_text("\n".join(lines))
        logger.info(f"✓ Auto-generated {env_file.name}")


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

            # Replace /EXTENSION_NAME placeholder in extension_router prefix if it exists
            if hasattr(ext_module, "extension_router"):
                router = ext_module.extension_router
                if hasattr(router, "prefix") and router.prefix == "/EXTENSION_NAME":
                    router.prefix = f"/extensions/{ext_name}"

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
