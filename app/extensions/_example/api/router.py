"""Example extension router - aggregates all extension endpoints."""

from fastapi import APIRouter

from . import features

router = APIRouter()
router.include_router(features.router)
