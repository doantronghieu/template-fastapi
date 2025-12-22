"""LangChain LLM provider implementation.

Implements LLMProvider using LangChain's universal initialization.
"""

from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.lib.llm.base import LLMProvider
from app.lib.llm.config import InvocationMode, Model, ModelProvider
from app.lib.llm.settings import llm_settings  # noqa: F401 - loads env into os.environ

# OpenRouter configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LangChainLLMProvider(LLMProvider):
    """LangChain implementation of the LLM provider."""

    def create_model(
        self,
        model: Annotated[Model | str, "Model enum or string identifier"],
        model_provider: Annotated[
            ModelProvider | str | None, "Provider (optional, can be inferred)"
        ] = None,
        temperature: Annotated[float, "Sampling temperature (0.0 to 1.0)"] = 0.0,
        tools: Annotated[list | None, "Tools to bind to the model"] = None,
        schema: Annotated[
            type[BaseModel] | None, "Pydantic model for structured output"
        ] = None,
        **kwargs,
    ) -> BaseChatModel:
        """Create chat model instance with optional tools and structured output."""
        model_value = model.value if isinstance(model, Model) else model
        provider_value = (
            model_provider.value
            if isinstance(model_provider, ModelProvider)
            else model_provider
        )

        # Force connection close after each request
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
            timeout=httpx.Timeout(300.0),
        )

        max_retries = kwargs.pop("max_retries", 2)

        # OpenRouter uses ChatOpenAI with custom base_url
        if provider_value == ModelProvider.OPENROUTER.value:
            chat_model = ChatOpenAI(
                model=model_value,
                api_key=llm_settings.OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=temperature,
                max_retries=max_retries,
                http_async_client=http_client,
                **kwargs,
            )
        else:
            chat_model = init_chat_model(
                model=model_value,
                model_provider=provider_value,
                temperature=temperature,
                max_retries=max_retries,
                http_async_client=http_client,
                **kwargs,
            )

        if tools:
            chat_model = chat_model.bind_tools(tools)

        if schema:
            method = "function_calling" if tools else None
            chat_model = (
                chat_model.with_structured_output(schema, method=method)
                if method
                else chat_model.with_structured_output(schema)
            )

        return chat_model

    async def invoke_model(
        self,
        prompt: Annotated[str | list[str], "Single prompt or list (for batch mode)"],
        mode: Annotated[
            InvocationMode | str, "Invocation mode: invoke, batch, stream"
        ] = InvocationMode.INVOKE,
        model: Annotated[BaseChatModel | None, "Pre-configured model instance"] = None,
        model_name: Annotated[
            Model | str | None, "Model identifier (required if model not provided)"
        ] = None,
        model_provider: Annotated[
            ModelProvider | str | None, "Provider identifier"
        ] = None,
        temperature: Annotated[float, "Sampling temperature (0.0 to 1.0)"] = 0.0,
        **kwargs,
    ) -> str | list[str] | AsyncIterator[str]:
        """Invoke LLM with specified execution mode."""
        if model is None:
            if model_name is None:
                raise ValueError("Must provide either 'model' or 'model_name'")
            model = self.create_model(model_name, model_provider, temperature, **kwargs)

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
