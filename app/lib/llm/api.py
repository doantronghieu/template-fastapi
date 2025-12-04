"""LLM provider test endpoints."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.lib.llm.config import InvocationMode
from app.lib.llm.dependencies import LLMProviderDep
from app.lib.llm.schemas import CreateModelRequest, InvokeModelRequest

router = APIRouter()


@router.post("/create-model", summary="Test Create Model")
async def test_create_model(req: CreateModelRequest, provider: LLMProviderDep):
    """Test creating a chat model via the configured provider."""
    llm = provider.create_model(
        model=req.model.value,
        model_provider=req.model_provider.value if req.model_provider else None,
        temperature=req.temperature,
    )
    return {
        "provider": type(provider).__name__,
        "model_created": True,
        "model_type": type(llm).__name__,
        "model_name": req.model.value,
    }


@router.post("/invoke", summary="Test Invoke Model")
async def test_invoke_model(req: InvokeModelRequest, provider: LLMProviderDep):
    """Test invoking a model with different modes via the configured provider."""
    result = await provider.invoke_model(
        req.prompt,
        mode=req.mode.value,
        model_name=req.model.value,
        model_provider=req.model_provider.value if req.model_provider else None,
        temperature=req.temperature,
    )

    if req.mode == InvocationMode.STREAM:

        async def generate():
            async for chunk in result:
                yield chunk

        return StreamingResponse(generate(), media_type="text/plain")

    return {"response": result}
