"""API endpoints for user operations."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.user import UserFullResponse
from app.services.user_service import UserServiceDep

router = APIRouter()


@router.get("/{user_id}", response_model=UserFullResponse)
async def get_user_details(
    user_id: UUID,
    service: UserServiceDep,
):
    """Get full user details including profile and all channels."""
    user = await service.get_user_details(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
