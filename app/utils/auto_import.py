"""Utilities for automatic module discovery and importing."""

import importlib
from pathlib import Path


def auto_import(init_file: str, package_name: str) -> None:
    """Auto-discover and import all modules (side-effect only).

    Used for tasks and models where import triggers registration.

    Args:
        init_file: __file__ from caller's __init__.py
        package_name: Full package name (e.g., "app.tasks")

    Example:
        from app.utils.auto_import import auto_import
        auto_import(__file__, "app.tasks")
    """
    package_dir = Path(init_file).parent
    module_files = [f.stem for f in package_dir.glob("*.py") if f.stem != "__init__"]

    for module_name in module_files:
        if not module_name.startswith("_"):
            importlib.import_module(f"{package_name}.{module_name}")
