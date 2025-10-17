"""Template Layer Configuration.

Jinja2Templates instance for server-side rendering.
Templates directory: templates/ at project root.

See docs/tech-stack.md for Jinja2 configuration and usage patterns.
See app/api/pages.py for page route implementations.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
