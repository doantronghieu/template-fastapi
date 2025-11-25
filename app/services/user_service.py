"""User service for user-related operations."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import SessionDep
from app.models import User
from app.services.base_crud import BaseCRUDService


class UserService(BaseCRUDService[User]):
    """
    Service for user-related operations.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_user_details(self, user_id: UUID) -> User:
        """Get full user details with channels eagerly loaded. Raises 404 if not found."""
        result = await self.session.execute(
            select(User).options(selectinload(User.channels)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        return user

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address. Returns None if not found."""
        return await self.get_by_field({"email": email})


# Dependency provider
async def get_user_service(session: SessionDep) -> UserService:
    """Provide UserService instance."""
    return UserService(session)


# Type alias for cleaner endpoint signatures
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
