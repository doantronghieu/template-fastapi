"""Auto-import all task modules for Celery discovery."""

import importlib
from pathlib import Path

# Get current directory
tasks_dir = Path(__file__).parent

# Auto-import all Python modules in tasks directory
for module_path in tasks_dir.glob("*.py"):
    module_name = module_path.stem
    # Skip __init__.py and private modules
    if module_name != "__init__" and not module_name.startswith("_"):
        importlib.import_module(f"app.tasks.{module_name}")
