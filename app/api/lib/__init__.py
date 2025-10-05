"""Library demo endpoints."""

from fastapi import APIRouter

from app.api.lib import langchain

router = APIRouter()
router.include_router(langchain.router, prefix="/langchain")
