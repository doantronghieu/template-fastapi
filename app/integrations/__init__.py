"""Integration loading utility for external service integrations.

Service-specific clients and adapters for external SaaS platforms and APIs.
Uses opt-out model: all integrations enabled by default, disable via DISABLED_INTEGRATIONS.
"""

import importlib
import logging
from pathlib import Path
from typing import Annotated, Literal

from app.core.config import settings

logger = logging.getLogger(__name__)

IntegrationHook = Literal["api", "webhooks", "tasks"]

# Integration directory for auto-discovery
_INTEGRATIONS_DIR = Path(__file__).parent


def discover_integrations() -> list[str]:
    """Auto-discover all integration modules in app/integrations/."""
    return [
        d.name
        for d in _INTEGRATIONS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "__init__.py").exists()
    ]


def get_enabled_integrations() -> list[str]:
    """Get enabled integrations (all discovered minus disabled)."""
    all_integrations = discover_integrations()
    disabled = settings.DISABLED_INTEGRATIONS or []
    return [name for name in all_integrations if name not in disabled]


def is_integration_enabled(
    name: Annotated[str, "Integration name to check"],
) -> bool:
    """Check if a specific integration is enabled."""
    return name not in (settings.DISABLED_INTEGRATIONS or [])


def get_integration_env_path(
    config_file_path: Annotated[str, "Pass __file__ from the config.py module"],
) -> str:
    """Get integration .env file path (envs/integrations/[name].env)."""
    integration_name = Path(config_file_path).parent.name
    project_root = Path(config_file_path).parent.parent.parent.parent
    env_file = project_root / "envs" / "integrations" / f"{integration_name}.env"
    return str(env_file)


def generate_integration_env(
    config_file_path: Annotated[str, "Pass __file__ from the config.py module"],
    settings_class: Annotated[type, "Pydantic Settings class to introspect"],
) -> None:
    """Generate .env template file for integration if it doesn't exist."""
    integration_name = Path(config_file_path).parent.name
    env_file = Path(get_integration_env_path(config_file_path))
    env_file.parent.mkdir(parents=True, exist_ok=True)

    if not env_file.exists():
        lines = [f"# {integration_name.upper()} Integration Configuration", ""]

        if hasattr(settings_class, "model_fields"):
            for field_name, field_info in settings_class.model_fields.items():
                description = field_info.description or field_name
                lines.append(f"# {description}")
                lines.append(f"{field_name}=")
                lines.append("")

        env_file.write_text("\n".join(lines))
        logger.info(f"✓ Auto-generated {env_file}")


def load_integrations(
    hook: Annotated[IntegrationHook, "Hook type: api, webhooks, or tasks"],
    *args,
    **kwargs,
) -> None:
    """Load enabled integrations for a specific hook (opt-out model)."""
    enabled_integrations = get_enabled_integrations()

    if not enabled_integrations:
        logger.debug("No integrations enabled (all disabled)")
        return

    for integration_name in enabled_integrations:
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

            if settings.DATABASE_ECHO:
                raise ImportError(error_msg) from e
            else:
                logger.warning(error_msg)
