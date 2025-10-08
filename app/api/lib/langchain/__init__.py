"""LangChain library demo endpoints."""

from fastapi import APIRouter

from app.api.lib.langchain.llm import router as llm_router
from app.core.openapi_tags import APITag

router = APIRouter()
router.include_router(llm_router, prefix="/llm", tags=[APITag.LANGCHAIN])
