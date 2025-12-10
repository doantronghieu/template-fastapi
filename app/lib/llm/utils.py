"""LLM resource loaders for prompts and schemas."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated


def load_prompt(
    name: Annotated[str, "Prompt filename without extension"],
    prompts_dir: Annotated[Path, "Directory containing prompt files"],
    **replacements: Annotated[str, "Placeholder replacements"],
) -> str:
    """Load prompt from markdown file and apply placeholder replacements."""
    path = prompts_dir / f"{name}.md"
    content = path.read_text()

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    return content


def create_loader(
    base_dir: Path,
) -> tuple[Callable[..., str], Callable[[str], dict]]:
    """Factory to create resource loaders for any LLM resource directory."""

    def _load_prompt(name: str, **replacements: str) -> str:
        return load_prompt(name, base_dir / "prompts", **replacements)

    def _load_schema(name: str) -> dict:
        path = base_dir / "schemas" / f"{name}.json"
        return json.loads(path.read_text())

    return _load_prompt, _load_schema


__all__ = ["create_loader", "load_prompt"]
