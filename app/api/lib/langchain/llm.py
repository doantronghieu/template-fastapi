"""LLM demo endpoints for testing langchain library functionality."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.lib.langchain import (
    InvocationMode,
    Model,
    ModelProvider,
    create_chat_model,
    invoke_model,
)

router = APIRouter()


class CreateModelRequest(BaseModel):
    model: Model = Model.GPT_OSS_20B
    model_provider: ModelProvider | None = ModelProvider.GROQ
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)


class InvokeModelRequest(BaseModel):
    prompt: str | list[str]
    mode: InvocationMode = InvocationMode.INVOKE
    model: Model = Model.GPT_OSS_20B
    model_provider: ModelProvider | None = ModelProvider.GROQ
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)


@router.post("/create-model")
async def test_create_chat_model(req: CreateModelRequest):
    """Test create_chat_model function."""
    llm = create_chat_model(
        model=req.model,
        model_provider=req.model_provider,
        temperature=req.temperature,
    )
    return {
        "model_created": True,
        "model_type": type(llm).__name__,
        "model_name": req.model.value,
    }


@router.post("/invoke")
async def test_invoke_model(req: InvokeModelRequest):
    """Test invoke_model function with different modes."""
    result = await invoke_model(
        req.prompt,
        mode=req.mode,
        model_name=req.model,
        model_provider=req.model_provider,
        temperature=req.temperature,
    )

    # Handle streaming mode differently
    if req.mode == InvocationMode.STREAM:

        async def generate():
            async for chunk in result:
                yield chunk

        return StreamingResponse(generate(), media_type="text/plain")

    # Return invoke/batch results as JSON
    return {"response": result}
