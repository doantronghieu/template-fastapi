"""LangChain LLM provider dependency injection."""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.langchain.llm import LangChainLLMProvider


def get_langchain_llm_provider() -> "LangChainLLMProvider":
    """Provide LangChain LLM provider instance.

    Returns:
        LangChain LLM provider instance

    Example:
        >>> @router.post("/langchain-specific")
        >>> async def endpoint(provider: LangChainLLMProviderDep):
        >>>     llm = provider.create_chat_model("gpt-5-nano", "openai")
        >>>     return {"model": type(llm).__name__}
    """
    from app.lib.langchain.llm import LangChainLLMProvider

    return LangChainLLMProvider()


# Type alias for dependency injection
LangChainLLMProviderDep = Annotated[
    "LangChainLLMProvider", Depends(get_langchain_llm_provider)
]
