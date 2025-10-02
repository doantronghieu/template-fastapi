from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.example import Example

router = APIRouter()


@router.get("/examples", response_model=list[Example])
async def get_examples(session: AsyncSession = Depends(get_session)):
    """Get all examples."""
    result = await session.execute(select(Example))
    return result.scalars().all()


@router.get("/examples/{example_id}", response_model=Example)
async def get_example(example_id: int, session: AsyncSession = Depends(get_session)):
    """Get example by ID."""
    result = await session.execute(select(Example).where(Example.id == example_id))
    return result.scalar_one_or_none()
