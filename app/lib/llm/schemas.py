"""LLM API request schemas."""

from pydantic import BaseModel, Field

from app.lib.llm.config import InvocationMode, Model, ModelProvider


class CreateModelRequest(BaseModel):
    """Request for testing model creation."""

    model: Model = Field(default=Model.GPT_OSS_20B, description="Model to create")
    model_provider: ModelProvider | None = Field(
        default=ModelProvider.GROQ, description="Model provider"
    )
    temperature: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Sampling temperature"
    )


class InvokeModelRequest(BaseModel):
    """Request for testing model invocation."""

    prompt: str | list[str] = Field(description="Prompt text or list for batch mode")
    mode: InvocationMode = Field(
        default=InvocationMode.INVOKE, description="Invocation mode"
    )
    model: Model = Field(default=Model.GPT_OSS_20B, description="Model to invoke")
    model_provider: ModelProvider | None = Field(
        default=ModelProvider.GROQ, description="Model provider"
    )
    temperature: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Sampling temperature"
    )
