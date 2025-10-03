"""Centralized dependency injection providers."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.database import async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide async database session."""
    async with async_session_maker() as session:
        yield session


def get_settings() -> Settings:
    """Provide application settings."""
    return settings


# Type aliases for cleaner endpoint signatures
SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
