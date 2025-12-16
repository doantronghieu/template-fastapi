"""LLM utilities for prompts, schemas, and retry handling."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)


def _is_rate_limit_error(exc: BaseException) -> bool:
    """Check if exception is a 429 rate limit error."""
    return getattr(exc, "status_code", None) == 429


def create_rate_limit_retry(
    max_retries: int = 6,
    min_wait: int = 1,
    max_wait: int = 60,
):
    """Create a retry decorator for rate limit errors (429)."""
    return retry(
        retry=retry_if_exception(_is_rate_limit_error),
        wait=wait_random_exponential(min=min_wait, max=max_wait),
        stop=stop_after_attempt(max_retries),
        reraise=True,
    )


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


__all__ = ["create_loader", "create_rate_limit_retry", "load_prompt"]
