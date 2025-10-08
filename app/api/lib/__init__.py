"""Library demo endpoints."""

from fastapi import APIRouter

from app.api.lib import langchain, llm
from app.core.openapi_tags import APITag

router = APIRouter()
router.include_router(langchain.router, prefix="/langchain")
router.include_router(llm.router, prefix="/llm", tags=[APITag.LLM])
