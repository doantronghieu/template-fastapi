"""Example model tests.

Demonstrates async database operations, SQLAlchemy queries, and API testing.
"""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.example import Example


async def test_create_example(db_session: AsyncSession):
    """Create example record and verify auto-generated ID."""
    example = Example(name="Test", description="Test description")
    db_session.add(example)
    await db_session.commit()
    await db_session.refresh(example)

    assert example.id is not None
    assert example.name == "Test"
    assert example.description == "Test description"


async def test_read_example(db_session: AsyncSession):
    """Query example record using select().where()."""
    example = Example(name="Read Test", description="Read description")
    db_session.add(example)
    await db_session.commit()

    result = await db_session.execute(
        select(Example).where(Example.name == "Read Test")
    )
    found_example = result.scalar_one()

    assert found_example.name == "Read Test"
    assert found_example.description == "Read description"


async def test_async_client(client: AsyncClient):
    """Test API endpoint with async HTTP client."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
