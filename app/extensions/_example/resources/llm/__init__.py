"""Example extension LLM resource loaders.

Extensions should copy this pattern to load their own prompts/schemas.
"""

from pathlib import Path

from app.lib.llm import create_loader

# Extension-specific loaders
LLM_RESOURCES_DIR = Path(__file__).parent
load_prompt, load_schema = create_loader(LLM_RESOURCES_DIR)

__all__ = ["load_prompt", "load_schema"]
