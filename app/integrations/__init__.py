"""Integration loading utility for external service integrations.

External service clients and third-party API integrations.

Service-specific clients and adapters for external SaaS platforms and APIs.

Use this module for integrations with external services that have
service-specific business logic and configuration.
"""

import importlib
import logging
from pathlib import Path
from typing import Literal

from app.core.config import settings

logger = logging.getLogger(__name__)

IntegrationHook = Literal["api", "webhooks", "tasks"]


def get_integration_env_path(config_file_path: str) -> str:
    """Get integration .env file path without generating it.

    Pattern: envs/integrations/[integration_name].env
    Example: app/integrations/messenger -> envs/integrations/messenger.env

    Args:
        config_file_path: Pass __file__ from the config.py module

    Returns:
        Path to the .env file in envs/integrations/
    """
    # Get integration folder name from config file path
    integration_name = Path(config_file_path).parent.name

    # Project root (3 levels up: config.py -> integration -> integrations -> app -> root)
    project_root = Path(config_file_path).parent.parent.parent.parent

    # .env file path in centralized envs directory
    env_file = project_root / "envs" / "integrations" / f"{integration_name}.env"

    return str(env_file)


def generate_integration_env(config_file_path: str, settings_class: type) -> None:
    """Generate .env file for integration if it doesn't exist.

    Introspects Settings class fields to create template.

    Args:
        config_file_path: Pass __file__ from the config.py module
        settings_class: Your Settings class

    Example:
        >>> # In app/integrations/messenger/config.py
        >>> class MessengerSettings(BaseSettings):
        ...     API_KEY: str = Field(default="", description="API key")
        >>> generate_integration_env(__file__, MessengerSettings)
    """
    # Get integration name
    integration_name = Path(config_file_path).parent.name

    # Get .env file path
    env_file = Path(get_integration_env_path(config_file_path))

    # Create envs/integrations directory if doesn't exist
    env_file.parent.mkdir(parents=True, exist_ok=True)

    # Auto-generate if doesn't exist
    if not env_file.exists():
        lines = [f"# {integration_name.upper()} Integration Configuration", ""]

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
        logger.info(f"✓ Auto-generated {env_file}")


def load_integrations(hook: IntegrationHook, *args, **kwargs) -> None:
    """Load enabled integrations for a specific hook.

    Args:
        hook: Integration hook to call (api, webhooks, tasks)
        *args, **kwargs: Passed to integration setup function

    Raises:
        ImportError: In development mode if integration fails to load

    Example:
        >>> from app.integrations import load_integrations
        >>> load_integrations("api", integration_router)
    """
    if not settings.ENABLED_INTEGRATIONS:
        return

    for integration_name in settings.ENABLED_INTEGRATIONS:
        try:
            integration_module = importlib.import_module(
                f"app.integrations.{integration_name}"
            )

            setup_func = getattr(integration_module, f"setup_{hook}", None)

            if setup_func and callable(setup_func):
                setup_func(*args, **kwargs)
                logger.info(f"✓ Loaded integration '{integration_name}' hook '{hook}'")
            else:
                logger.debug(f"Integration '{integration_name}' has no '{hook}' hook")

        except ImportError as e:
            error_msg = (
                f"Integration '{integration_name}' failed to load hook '{hook}': {e}"
            )

            # Fail fast in development (when DATABASE_ECHO=True)
            if settings.DATABASE_ECHO:
                raise ImportError(error_msg) from e
            else:
                logger.warning(error_msg)
