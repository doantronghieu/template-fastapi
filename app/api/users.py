"""API endpoints for user operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import PaginationParams
from app.schemas.user import UserCreate, UserDetailResponse, UserFullResponse, UserUpdate
from app.services import PaginatedResponse, PaginationType
from app.services.user_service import UserServiceDep

router = APIRouter()


@router.post("/", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    service: UserServiceDep,
):
    """Create a new user."""
    user = await service.create(user_in)
    return user


@router.get("/", response_model=PaginatedResponse)
async def list_users(
    service: UserServiceDep,
    pagination: Annotated[PaginationParams, Depends()],
    role: str | None = Query(None, description="Filter by role"),
    email_like: str | None = Query(None, description="Filter by email pattern"),
):
    """List users with pagination and filtering."""
    filters = {}
    if role:
        filters["role"] = role
    if email_like:
        filters["email__ilike"] = f"%{email_like}%"

    result = await service.get_multi(
        limit=pagination.limit or 10,
        offset=pagination.offset or 0,
        cursor=pagination.cursor,
        pagination_type=pagination.pagination_type or PaginationType.OFFSET,
        order_by=pagination.order_by,
        filters=filters if filters else None,
    )
    return result


@router.get("/{user_id}", response_model=UserFullResponse)
async def get_user_details(
    user_id: UUID,
    service: UserServiceDep,
):
    """Get full user details including profile and all channels."""
    user = await service.get_user_details(user_id)

    if not user:
        raise HTTPException(404, f"User {user_id} not found")
        
    return user

@router.get("/{user_id}/simple", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    service: UserServiceDep,
):
    """Get user by ID without eager-loading relationships."""
    user = await service.get_by_id(user_id)
    return user


@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    service: UserServiceDep,
):
    """Update user (partial update)."""
    user = await service.update(user_id, user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: UserServiceDep,
):
    """Delete user by ID."""
    await service.delete(user_id)
    return None
