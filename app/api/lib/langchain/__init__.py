"""LangChain library demo endpoints."""

from fastapi import APIRouter

from app.api.lib.langchain.llm import router as llm_router

router = APIRouter()
router.include_router(llm_router, prefix="/llm", tags=["lib-langchain-llm"])
