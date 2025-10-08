"""Shared schemas for library test endpoints."""

from pydantic import BaseModel, Field

from app.lib.llm import InvocationMode, Model, ModelProvider


class CreateModelRequest(BaseModel):
    """Request schema for testing model creation."""

    model: Model = Model.GPT_OSS_20B
    model_provider: ModelProvider | None = ModelProvider.GROQ
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)


class InvokeModelRequest(BaseModel):
    """Request schema for testing model invocation."""

    prompt: str | list[str]
    mode: InvocationMode = InvocationMode.INVOKE
    model: Model = Model.GPT_OSS_20B
    model_provider: ModelProvider | None = ModelProvider.GROQ
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
