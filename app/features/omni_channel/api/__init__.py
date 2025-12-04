"""API router for omni-channel feature.

Combines users and messaging endpoints into single router.
"""

from fastapi import APIRouter

from . import messaging, users

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(messaging.router, prefix="/messaging", tags=["Messaging"])
