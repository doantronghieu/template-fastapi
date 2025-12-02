"""LLM provider dependency injection."""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.llm.base import LLMProvider


def get_llm_provider() -> "LLMProvider":
    """Get configured LLM provider instance based on LLM_PROVIDER setting."""
    from app.lib.llm.factory import get_llm_provider as factory_get_provider

    return factory_get_provider()


# Type alias for dependency injection
LLMProviderDep = Annotated["LLMProvider", Depends(get_llm_provider)]
