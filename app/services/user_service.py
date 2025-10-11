"""User service for user-related operations."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import SessionDep
from app.models import User


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_details(self, user_id: UUID) -> User | None:
        """
        Get full user details with channels.

        Args:
            user_id: User UUID

        Returns:
            User with channels loaded, or None if not found
        """
        result = await self.session.execute(
            select(User).options(selectinload(User.channels)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


# Dependency provider
async def get_user_service(session: SessionDep) -> UserService:
    """Provide UserService instance."""
    return UserService(session)


# Type alias for cleaner endpoint signatures
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
