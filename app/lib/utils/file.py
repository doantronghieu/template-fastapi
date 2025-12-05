"""File utilities for reading and writing files."""

from pathlib import Path
from typing import Annotated


def read_file(path: Annotated[Path | str, "File path to read"]) -> str:
    """Read file content with error handling."""
    file_path = Path(path) if isinstance(path, str) else path
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.read_text(encoding="utf-8")
