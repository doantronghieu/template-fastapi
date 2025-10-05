"""LangChain LLM initialization utilities.

Provides reusable functions for creating and configuring chat models
across different providers using LangChain's universal initialization.
"""

from collections.abc import AsyncIterator

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.lib.langchain.config import InvocationMode, Model, ModelProvider


def create_chat_model(
    model: Model,
    model_provider: ModelProvider | None = None,
    temperature: float = 0.0,
    **kwargs,
) -> BaseChatModel:
    """Create chat model instance using universal initialization.

    Args:
        model: Model enum value
        model_provider: Provider enum value (optional, can be inferred from model)
        temperature: Sampling temperature (0.0 to 1.0)
        **kwargs: Additional model-specific parameters

    Returns:
        Configured chat model instance

    Example:
        >>> from app.lib.langchain import Model, ModelProvider
        >>> llm = create_chat_model(Model.GPT_5_NANO, ModelProvider.OPENAI)
        >>> response = llm.invoke("Hello!")
    """
    return init_chat_model(
        model=model.value,
        model_provider=model_provider.value if model_provider else None,
        temperature=temperature,
        **kwargs,
    )


async def invoke_model(
    prompt: str | list[str],
    mode: InvocationMode = InvocationMode.INVOKE,
    model: BaseChatModel | None = None,
    model_name: Model | None = None,
    model_provider: ModelProvider | None = None,
    temperature: float = 0.0,
    **kwargs,
) -> str | list[str] | AsyncIterator[str]:
    """Invoke LLM with different execution modes.

    Args:
        prompt: Single prompt string or list of prompts (for BATCH mode)
        mode: Invocation mode (INVOKE, BATCH, or STREAM)
        model: Pre-configured chat model instance (optional)
        model_name: Model enum value (required if model not provided)
        model_provider: Provider enum value (optional)
        temperature: Sampling temperature (0.0 to 1.0)
        **kwargs: Additional model-specific parameters

    Returns:
        - INVOKE mode: Single response string
        - BATCH mode: List of response strings
        - STREAM mode: AsyncIterator yielding response chunks

    Raises:
        ValueError: If neither model nor model_name provided, or prompt type doesn't match mode

    Example:
        >>> # With pre-created model
        >>> llm = create_chat_model(Model.GPT_5_NANO, temperature=0.7)
        >>> response = await invoke_model("Hello!", model=llm)
        >>>
        >>> # With model creation params
        >>> response = await invoke_model(
        ...     "Hello!",
        ...     model_name=Model.GPT_5_NANO,
        ...     model_provider=ModelProvider.OPENAI,
        ...     temperature=0.7
        ... )
        >>>
        >>> # Batch mode
        >>> responses = await invoke_model(
        ...     ["Q1", "Q2"],
        ...     mode=InvocationMode.BATCH,
        ...     model_name=Model.GPT_5_NANO
        ... )
        >>>
        >>> # Streaming
        >>> stream = await invoke_model(
        ...     "Write a story",
        ...     mode=InvocationMode.STREAM,
        ...     model_name=Model.GPT_OSS_120B
        ... )
        >>> async for chunk in stream:
        ...     print(chunk, end="", flush=True)
    """
    if model is None:
        if model_name is None:
            raise ValueError("Must provide either 'model' or 'model_name'")
        model = create_chat_model(model_name, model_provider, temperature, **kwargs)

    if mode == InvocationMode.INVOKE:
        if isinstance(prompt, list):
            raise ValueError("INVOKE mode requires a single prompt string, not a list")
        response = await model.ainvoke(prompt)
        return response.content

    elif mode == InvocationMode.BATCH:
        if not isinstance(prompt, list):
            raise ValueError("BATCH mode requires a list of prompts")
        responses = await model.abatch(prompt)
        return [r.content for r in responses]

    elif mode == InvocationMode.STREAM:
        if isinstance(prompt, list):
            raise ValueError("STREAM mode requires a single prompt string, not a list")

        async def stream_generator() -> AsyncIterator[str]:
            async for chunk in model.astream(prompt):
                if chunk.content:
                    yield chunk.content

        return stream_generator()
