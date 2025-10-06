"""LLM resource loaders for prompts and schemas.

Provides:
- create_loader(): Factory for creating resource loaders (for extensions)
- load_prompt(): Load core app prompts
- load_schema(): Load core app schemas
"""

from pathlib import Path
import json


def create_loader(base_dir: Path):
    """Factory to create resource loaders for any LLM resource directory.

    Args:
        base_dir: Path to LLM resources directory (containing prompts/ and schemas/)

    Returns:
        Tuple of (load_prompt, load_schema) functions
    """

    def load_prompt(name: str, **replacements: str) -> str:
        """Load prompt from prompts/{name}.md and replace placeholders.

        Args:
            name: Prompt filename without extension
            **replacements: Placeholder values (e.g., CURRENT_TIME='2025-10-06')

        Returns:
            Prompt content with placeholders replaced
        """
        path = base_dir / "prompts" / f"{name}.md"
        content = path.read_text()

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        return content

    def load_schema(name: str) -> dict:
        """Load JSON schema from schemas/{name}.json"""
        path = base_dir / "schemas" / f"{name}.json"
        return json.loads(path.read_text())

    return load_prompt, load_schema


# Core app loaders
LLM_RESOURCES_DIR = Path(__file__).parent
load_prompt, load_schema = create_loader(LLM_RESOURCES_DIR)

__all__ = ["create_loader", "load_prompt", "load_schema"]
