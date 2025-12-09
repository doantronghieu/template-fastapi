"""LLM resource loaders for prompts and schemas."""

import json
from collections.abc import Callable
from pathlib import Path


def create_loader(
    base_dir: Path,
) -> tuple[Callable[..., str], Callable[[str], dict]]:
    """Factory to create resource loaders for any LLM resource directory."""

    def load_prompt(name: str, **replacements: str) -> str:
        """Load prompt from prompts/{name}.md and replace placeholders."""
        path = base_dir / "prompts" / f"{name}.md"
        content = path.read_text()

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        return content

    def load_schema(name: str) -> dict:
        """Load JSON schema from schemas/{name}.json."""
        path = base_dir / "schemas" / f"{name}.json"
        return json.loads(path.read_text())

    return load_prompt, load_schema


__all__ = ["create_loader"]
