"""LangChain LLM provider implementation and utilities.

Implements LLMProvider protocol using LangChain's universal initialization.
"""

from collections.abc import AsyncIterator

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from app.lib.llm.base import LLMProvider
from app.lib.llm.config import InvocationMode, Model, ModelProvider


class LangChainLLMProvider(LLMProvider):
    """LangChain implementation of the LLM provider protocol."""

    def create_model(
        self,
        model: Model | str,
        model_provider: ModelProvider | str | None = None,
        temperature: float = 0.0,
        tools: list | None = None,
        schema: type[BaseModel] | None = None,
        **kwargs,
    ) -> BaseChatModel:
        """Create chat model instance with optional tools and structured output.

        Args:
            model: Model enum or string identifier
            model_provider: Provider enum/string (optional, can be inferred)
            temperature: Sampling temperature (0.0 to 1.0)
            tools: Optional list of tools to bind to the model
            schema: Optional Pydantic model class for structured output
            **kwargs: Additional model-specific parameters

        Returns:
            Configured chat model instance

        Examples:
            >>> provider = LangChainLLMProvider()
            >>> # Basic model
            >>> llm = provider.create_model(Model.GPT_5_NANO)
            >>> # With tools
            >>> llm = provider.create_model(Model.GPT_OSS_120B, tools=[calculator])
            >>> # With structured output
            >>> llm = provider.create_model(
            ...     Model.GPT_OSS_120B,
            ...     schema=BookingExtractionSchema
            ... )
        """
        # Extract enum values if needed
        model_value = model.value if isinstance(model, Model) else model
        provider_value = (
            model_provider.value
            if isinstance(model_provider, ModelProvider)
            else model_provider
        )

        # Create base model
        chat_model: BaseChatModel = init_chat_model(
            model=model_value,
            model_provider=provider_value,
            temperature=temperature,
            **kwargs,
        )

        # Apply tools if provided
        if tools:
            chat_model = chat_model.bind_tools(tools)

        # Apply structured output if provided
        if schema:
            # Use function_calling method when tools are present for compatibility
            if tools:
                chat_model = chat_model.with_structured_output(
                    schema, method="function_calling"
                )
            else:
                chat_model = chat_model.with_structured_output(schema)

        return chat_model

    async def invoke_model(
        self,
        prompt: str | list[str],
        mode: InvocationMode | str = InvocationMode.INVOKE,
        model: BaseChatModel | None = None,
        model_name: Model | str | None = None,
        model_provider: ModelProvider | str | None = None,
        temperature: float = 0.0,
        **kwargs,
    ) -> str | list[str] | AsyncIterator[str]:
        """Invoke LLM with different execution modes.

        Args:
            prompt: Single prompt string or list of prompts (for BATCH mode)
            mode: Invocation mode enum or string ("invoke", "batch", "stream")
            model: Pre-configured chat model instance (optional)
            model_name: Model enum or string (required if model not provided)
            model_provider: Provider enum or string (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional model-specific parameters

        Returns:
            - INVOKE mode: Single response string
            - BATCH mode: List of response strings
            - STREAM mode: AsyncIterator yielding response chunks

        Raises:
            ValueError: If neither model nor model_name provided, or prompt type doesn't match mode

        Example:
            >>> provider = LangChainLLMProvider()
            >>> # Direct invocation
            >>> response = await provider.invoke_model("Hello!", model_name=Model.GPT_5_NANO)
            >>>
            >>> # Batch mode
            >>> responses = await provider.invoke_model(
            ...     ["Q1", "Q2"],
            ...     mode=InvocationMode.BATCH,
            ...     model_name=Model.GPT_5_NANO
            ... )
            >>>
            >>> # Streaming
            >>> stream = await provider.invoke_model(
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
            model = self.create_chat_model(
                model_name, model_provider, temperature, **kwargs
            )

        # Convert string to enum if needed
        mode_enum = InvocationMode(mode) if isinstance(mode, str) else mode

        if mode_enum == InvocationMode.INVOKE:
            if isinstance(prompt, list):
                raise ValueError(
                    "INVOKE mode requires a single prompt string, not a list"
                )
            response = await model.ainvoke(prompt)
            return response.content

        elif mode_enum == InvocationMode.BATCH:
            if not isinstance(prompt, list):
                raise ValueError("BATCH mode requires a list of prompts")
            responses = await model.abatch(prompt)
            return [r.content for r in responses]

        elif mode_enum == InvocationMode.STREAM:
            if isinstance(prompt, list):
                raise ValueError(
                    "STREAM mode requires a single prompt string, not a list"
                )

            async def stream_generator() -> AsyncIterator[str]:
                async for chunk in model.astream(prompt):
                    if chunk.content:
                        yield chunk.content

            return stream_generator()
