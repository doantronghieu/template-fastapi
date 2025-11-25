"""Example service demonstrating dependency injection pattern."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import SessionDep
from app.models.example import Example


class ExampleService:
    """Service layer for Example business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Example]:
        """Retrieve all examples."""
        result = await self.session.execute(select(Example))
        return list(result.scalars().all())

    async def get_by_id(self, example_id: int) -> Example | None:
        """Retrieve example by ID."""
        result = await self.session.execute(
            select(Example).where(Example.id == example_id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, description: str | None = None) -> Example:
        """Create new example."""
        example = Example(name=name, description=description)
        self.session.add(example)
        await self.session.commit()
        await self.session.refresh(example)
        return example

    async def delete(self, example_id: int) -> bool:
        """Delete example by ID. Returns True if deleted, False if not found."""
        example = await self.get_by_id(example_id)
        if not example:
            return False
        await self.session.delete(example)
        await self.session.commit()
        return True


async def get_example_service(session: SessionDep) -> ExampleService:
    """Provide ExampleService instance."""
    return ExampleService(session)


# Type alias for cleaner endpoint signatures
ExampleServiceDep = Annotated[ExampleService, Depends(get_example_service)]
