"""Example feature service - business logic layer."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.dependencies import SessionDep
from app.extensions._example.models import ExampleFeature
from app.extensions._example.schemas.feature import (
    ExampleFeatureCreate,
    ExampleFeatureUpdate,
)

from app.extensions._example.config import extension_settings


class ExampleFeatureService:
    """Service for managing example features."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[ExampleFeature]:
        """Get all example features.

        Note: Uses extension config - api_key available via extension_settings.
        """
        # Example: Access extension config
        api_key = extension_settings.EXAMPLE_API_KEY
        _ = api_key
        result = await self.session.execute(select(ExampleFeature))
        return list(result.scalars().all())

    async def get_by_id(self, feature_id: int) -> ExampleFeature | None:
        """Get example feature by ID."""
        return await self.session.get(ExampleFeature, feature_id)

    async def create(self, data: ExampleFeatureCreate) -> ExampleFeature:
        """Create new example feature."""
        feature = ExampleFeature(**data.model_dump())
        self.session.add(feature)
        await self.session.commit()
        await self.session.refresh(feature)
        return feature

    async def update(
        self, feature_id: int, data: ExampleFeatureUpdate
    ) -> ExampleFeature | None:
        """Update example feature."""
        feature = await self.get_by_id(feature_id)
        if not feature:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(feature, key, value)

        self.session.add(feature)
        await self.session.commit()
        await self.session.refresh(feature)
        return feature

    async def delete(self, feature_id: int) -> bool:
        """Delete example feature."""
        feature = await self.get_by_id(feature_id)
        if not feature:
            return False

        await self.session.delete(feature)
        await self.session.commit()
        return True


def get_example_feature_service(session: SessionDep) -> ExampleFeatureService:
    """Dependency provider for ExampleFeatureService."""
    return ExampleFeatureService(session)


ExampleFeatureServiceDep = Annotated[
    ExampleFeatureService, Depends(get_example_feature_service)
]
