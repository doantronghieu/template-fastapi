"""LLM provider dependency injection."""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.llm.base import LLMProvider


def get_llm_provider() -> "LLMProvider":
    """Provide configured LLM provider instance based on settings.

    Uses factory pattern to return the appropriate provider
    based on LLM_PROVIDER setting.

    Returns:
        LLM provider instance (e.g., LangChainProvider)

    Example:
        >>> @router.post("/chat")
        >>> async def chat(prompt: str, provider: LLMProviderDep):
        >>>     response = await provider.invoke_model(prompt, model_name="gpt-5-nano")
        >>>     return {"response": response}
    """
    from app.lib.llm.factory import get_llm_provider as factory_get_provider

    return factory_get_provider()


# Type alias for dependency injection
LLMProviderDep = Annotated["LLMProvider", Depends(get_llm_provider)]
