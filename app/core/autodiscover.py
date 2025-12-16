"""Unified auto-discovery system using file naming conventions.

Supports features (auto), extensions (opt-in), integrations (opt-out), and lib (auto).
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
from enum import StrEnum
from functools import wraps
from pathlib import Path
from types import ModuleType as PyModuleType
from typing import TYPE_CHECKING, Annotated, Any, Callable, TypeVar

from dotenv import load_dotenv

# Load .env early for direct os.environ reads (avoids circular import with settings)
load_dotenv()

if TYPE_CHECKING:
    from fastapi import APIRouter
    from pydantic_settings import BaseSettings
    from sqladmin import Admin

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class ModuleType(StrEnum):
    """Discoverable module types with their corresponding discovery models."""

    FEATURES = "features"
    EXTENSIONS = "extensions"
    INTEGRATIONS = "integrations"
    LIB = "lib"


# =============================================================================
# Internal Helpers
# =============================================================================


def _strip_inline_comment(val: str) -> str:
    """Strip inline comments (# ...) from env values."""
    if "#" in val:
        val = val.split("#")[0]
    return val.strip()


def _get_disabled_list_from_env() -> list[str]:
    """Read DISABLED_INTEGRATIONS from env (avoids circular import with settings)."""
    val = _strip_inline_comment(os.environ.get("DISABLED_INTEGRATIONS", ""))
    if not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


def _get_enabled_list_from_env() -> list[str]:
    """Read ENABLED_EXTENSIONS from env (avoids circular import with settings)."""
    val = _strip_inline_comment(os.environ.get("ENABLED_EXTENSIONS", ""))
    if not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


def _is_debug_mode() -> bool:
    """Check if debug mode is enabled (for error handling decisions)."""
    return os.environ.get("DATABASE_ECHO", "").lower() in ("true", "1", "yes")


def _format_tag(name: str, template: str) -> str:
    """Format a tag template with module name variations."""
    return template.format(name=name, Name=name.replace("_", " ").title())


def _build_module_path(
    module_type: ModuleType, module_name: str, submodule: str
) -> str:
    """Build full Python module path."""
    return f"app.{module_type.value}.{module_name}.{submodule}"


def _has_submodule(module_dir: Path, submodule: str) -> bool:
    """Check if submodule exists as file or package."""
    return (module_dir / f"{submodule}.py").exists() or (
        module_dir / submodule / "__init__.py"
    ).exists()


def _safe_import(
    module_path: str,
    *,
    reraise_in_debug: bool = True,
) -> PyModuleType | None:
    """Safely import a module with error handling.

    Returns None on ImportError (logs warning), re-raises in debug mode if requested.
    """
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        if reraise_in_debug and _is_debug_mode():
            raise
        logger.warning(f"Failed to load {module_path}: {e}")
        return None


# =============================================================================
# Discovery Functions
# =============================================================================


def get_module_dirs(
    module_type: ModuleType,
    *,
    enabled: Annotated[list[str] | None, "opt-in list, takes precedence"] = None,
    disabled: Annotated[list[str] | None, "opt-out list"] = None,
    use_settings: Annotated[bool, "apply env var filters based on module type"] = True,
) -> list[Path]:
    """Get directories to scan based on module type and filter lists."""
    base_path = Path(__file__).parent.parent / module_type.value

    if not base_path.exists():
        return []

    dirs = [
        d for d in base_path.iterdir() if d.is_dir() and (d / "__init__.py").exists()
    ]

    # Apply filters from env vars if none provided
    if use_settings and enabled is None and disabled is None:
        if module_type == ModuleType.EXTENSIONS:
            enabled = _get_enabled_list_from_env()
        elif module_type == ModuleType.INTEGRATIONS:
            disabled = _get_disabled_list_from_env()
        # FEATURES and LIB: all enabled by default (no filter)

    # Opt-in model (enabled list takes precedence)
    if enabled is not None:
        dirs = [d for d in dirs if d.name in enabled]
    # Opt-out model (all except disabled)
    elif disabled is not None:
        dirs = [d for d in dirs if d.name not in disabled]

    return sorted(dirs, key=lambda d: d.name)


def discover_modules(module_type: ModuleType) -> list[str]:
    """Auto-discover all module names in app/{module_type}/ (no filtering)."""
    return [d.name for d in get_module_dirs(module_type, use_settings=False)]


def get_enabled_modules(module_type: ModuleType) -> list[str]:
    """Get enabled module names based on discovery model."""
    return [d.name for d in get_module_dirs(module_type, use_settings=True)]


# =============================================================================
# Runtime Functions
# =============================================================================


class ModuleDisabledError(Exception):
    """Raised when trying to use a disabled module."""

    def __init__(
        self,
        module_type: ModuleType,
        name: Annotated[str, "name of disabled module"],
        message: Annotated[str | None, "custom error message"] = None,
    ):
        self.module_type = module_type
        self.name = name
        if message:
            msg = message
        elif module_type == ModuleType.INTEGRATIONS:
            msg = (
                f"Integration '{name}' is disabled. Remove from DISABLED_INTEGRATIONS."
            )
        elif module_type == ModuleType.EXTENSIONS:
            msg = f"Extension '{name}' is disabled. Add to ENABLED_EXTENSIONS."
        else:
            msg = f"Module '{module_type.value}/{name}' is disabled."
        super().__init__(msg)


def is_module_enabled(module_type: ModuleType, name: str) -> bool:
    """Check if a specific module is enabled based on discovery model."""
    return name in get_enabled_modules(module_type)


def require_module(module_type: ModuleType, name: str) -> Callable[[F], F]:
    """Decorator that enforces module is enabled at decoration time.

    Raises ModuleDisabledError immediately when module loads if disabled.
    """

    def decorator(func: F) -> F:
        if not is_module_enabled(module_type, name):
            raise ModuleDisabledError(module_type, name)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


# =============================================================================
# Environment Utilities
# =============================================================================


def get_module_env_path(
    module_type: ModuleType,
    config_file_path: Annotated[str, "pass __file__ from config.py"],
) -> str:
    """Get module .env file path (pattern: envs/{module_type}/{name}.env)."""
    module_name = Path(config_file_path).parent.name
    # Project root (4 levels up: config.py -> module -> module_type -> app -> root)
    project_root = Path(config_file_path).parent.parent.parent.parent
    env_file = project_root / "envs" / module_type.value / f"{module_name}.env"
    return str(env_file)


def generate_module_env(
    module_type: ModuleType,
    config_file_path: Annotated[str, "pass __file__ from config.py"],
    settings_class: Annotated[
        type[BaseSettings], "Pydantic Settings class to introspect"
    ],
) -> None:
    """Generate .env template file for module if it doesn't exist."""
    module_name = Path(config_file_path).parent.name
    env_file = Path(get_module_env_path(module_type, config_file_path))

    env_file.parent.mkdir(parents=True, exist_ok=True)

    if not env_file.exists():
        type_label = module_type.value.rstrip("s").title()
        lines = [f"# {module_name.upper()} {type_label} Configuration", ""]

        if hasattr(settings_class, "model_fields"):
            for field_name, field_info in settings_class.model_fields.items():
                description = field_info.description or field_name
                lines.extend([f"# {description}", f"{field_name}=", ""])

        env_file.write_text("\n".join(lines))
        logger.info(f"✓ Auto-generated {env_file}")


# =============================================================================
# Autodiscover Functions
# =============================================================================


def autodiscover_routers(
    module_type: ModuleType,
    parent_router: APIRouter,
    *,
    enabled: Annotated[list[str] | None, "opt-in filter"] = None,
    disabled: Annotated[list[str] | None, "opt-out filter"] = None,
    prefix_template: Annotated[str, "{name} replaced with module name"] = "/{name}",
    tags_template: Annotated[
        str | None, "{Name}=title case, {name}=lowercase"
    ] = "{Name}",
    file_name: str = "router.py",
    include_in_schema: bool = True,
) -> list[str]:
    """Auto-discover and register router.py from modules."""
    registered = []
    submodule = file_name[:-3]  # Remove .py extension

    for module_dir in get_module_dirs(module_type, enabled=enabled, disabled=disabled):
        if not _has_submodule(module_dir, submodule):
            continue

        module_path = _build_module_path(module_type, module_dir.name, submodule)
        module = _safe_import(module_path)

        if module and hasattr(module, "router"):
            prefix = prefix_template.format(name=module_dir.name)
            tags = (
                [_format_tag(module_dir.name, tags_template)] if tags_template else None
            )
            parent_router.include_router(
                module.router,
                prefix=prefix,
                tags=tags,
                include_in_schema=include_in_schema,
            )
            registered.append(module_dir.name)

    if registered:
        logger.info(f"✓ Routers [{module_type.value}]: {', '.join(registered)}")

    return registered


def autodiscover_webhooks(
    module_type: ModuleType,
    parent_router: APIRouter,
    *,
    enabled: Annotated[list[str] | None, "opt-in filter"] = None,
    disabled: Annotated[list[str] | None, "opt-out filter"] = None,
    prefix_template: str = "/{name}",
    tags_template: str | None = "{Name} Webhooks",
) -> list[str]:
    """Auto-discover and register webhooks.py from modules."""
    registered = []

    for module_dir in get_module_dirs(module_type, enabled=enabled, disabled=disabled):
        if not _has_submodule(module_dir, "webhooks"):
            continue

        module_path = _build_module_path(module_type, module_dir.name, "webhooks")
        module = _safe_import(module_path)

        if module and hasattr(module, "router"):
            prefix = prefix_template.format(name=module_dir.name)
            tags = (
                [_format_tag(module_dir.name, tags_template)] if tags_template else None
            )
            parent_router.include_router(module.router, prefix=prefix, tags=tags)
            registered.append(module_dir.name)

    if registered:
        logger.info(f"✓ Webhooks [{module_type.value}]: {', '.join(registered)}")

    return registered


def autodiscover_models(
    module_type: ModuleType,
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
) -> list[str]:
    """Auto-import models.py for Alembic discovery."""
    imported = []

    for module_dir in get_module_dirs(module_type, enabled=enabled, disabled=disabled):
        if not _has_submodule(module_dir, "models"):
            continue

        module_path = _build_module_path(module_type, module_dir.name, "models")
        if _safe_import(module_path):
            imported.append(module_dir.name)
            logger.debug(f"✓ Models: {module_type.value}/{module_dir.name}")

    return imported


def autodiscover_tasks(
    module_type: ModuleType,
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
) -> list[str]:
    """Auto-discover tasks.py module paths for Celery (returns paths, no import)."""
    task_modules = []

    for module_dir in get_module_dirs(module_type, enabled=enabled, disabled=disabled):
        if _has_submodule(module_dir, "tasks"):
            module_path = _build_module_path(module_type, module_dir.name, "tasks")
            task_modules.append(module_path)
            logger.debug(f"✓ Tasks: {module_type.value}/{module_dir.name}")

    return task_modules


def autodiscover_admin(
    module_type: ModuleType,
    admin: Admin,
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
) -> list[str]:
    """Auto-discover and register admin.py ModelView classes."""
    from sqladmin import ModelView

    registered = []

    for module_dir in get_module_dirs(module_type, enabled=enabled, disabled=disabled):
        if not _has_submodule(module_dir, "admin"):
            continue

        module_path = _build_module_path(module_type, module_dir.name, "admin")
        module = _safe_import(module_path)

        if module:
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, ModelView)
                    and obj is not ModelView
                    and hasattr(obj, "model")
                    and obj.model is not None
                ):
                    admin.add_view(obj)
                    registered.append(name)
                    logger.debug(f"✓ Admin: {name}")

    return registered


def autodiscover_beat_schedules(
    module_type: ModuleType,
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
) -> dict[str, Any]:
    """Auto-discover Celery beat schedules from schedules.py (SCHEDULES dict)."""
    schedules: dict[str, Any] = {}
    discovered: list[str] = []

    for module_dir in get_module_dirs(module_type, enabled=enabled, disabled=disabled):
        schedules_file = module_dir / "schedules.py"
        if not schedules_file.exists():
            continue

        module_path = f"app.{module_type.value}.{module_dir.name}.schedules"
        module = _safe_import(module_path, reraise_in_debug=False)

        if module and hasattr(module, "SCHEDULES"):
            for key, value in module.SCHEDULES.items():
                prefixed_key = f"{module_dir.name}.{key}"
                schedules[prefixed_key] = value
            discovered.append(module_dir.name)

    if discovered:
        logger.info(f"✓ Schedules [{module_type.value}]: {', '.join(discovered)}")

    return schedules


def auto_import_modules(
    module_type: ModuleType,
    submodule: Annotated[str, "submodule name to import (e.g., 'tasks', 'models')"],
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
) -> list[str]:
    """Auto-discover and import submodules for side-effect registration."""
    imported = []

    for module_dir in get_module_dirs(module_type, enabled=enabled, disabled=disabled):
        if not _has_submodule(module_dir, submodule):
            continue

        module_path = _build_module_path(module_type, module_dir.name, submodule)
        if _safe_import(module_path):
            imported.append(module_path)
            logger.debug(f"✓ Imported: {module_path}")

    return imported
