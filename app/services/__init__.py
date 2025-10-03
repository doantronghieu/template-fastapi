"""Service layer for business logic with auto-discovery."""

import importlib
from pathlib import Path

# Auto-discover and import all service modules
_services_dir = Path(__file__).parent
_service_modules = [f.stem for f in _services_dir.glob("*.py") if f.stem != "__init__"]

# Dynamically import all services and collect exports
__all__ = []
for module_name in _service_modules:
    module = importlib.import_module(f"app.services.{module_name}")

    # Import all public members (classes, functions)
    for attr_name in dir(module):
        if not attr_name.startswith("_"):
            attr = getattr(module, attr_name)
            globals()[attr_name] = attr
            __all__.append(attr_name)
