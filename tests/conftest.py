"""Pytest Configuration and Fixtures.

Provides test fixtures: test_engine, db_session, client, sync_client.
Test database: {POSTGRES_DB}_test on Supabase with transaction rollback isolation.

See docs/tech-stack.md for pytest configuration and fixture details.
See tests/README.md for detailed usage guide and examples.
"""

from collections.abc import AsyncGenerator

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    AsyncTransaction,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

import os

# Enable _example extension for testing (before app import)
os.environ.setdefault("ENABLED_EXTENSIONS", "_example")

from app.core.config import settings  # noqa: E402
from app.dependencies import get_session  # noqa: E402
from app.main import app  # noqa: E402

# Test database URL - automatically uses {POSTGRES_DB}_test
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    f"/{settings.POSTGRES_DB}", f"/{settings.POSTGRES_DB}_test"
)

# Postgres URL (for creating test database)
POSTGRES_URL = settings.DATABASE_URL.replace(f"/{settings.POSTGRES_DB}", "/postgres")


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Session-scoped async database engine.

    Creates test database if it doesn't exist, creates tables once at session
    start, drops at end. Uses NullPool to avoid connection pooling issues.
    """
    # Create test database if it doesn't exist
    postgres_engine = create_async_engine(
        POSTGRES_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with postgres_engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(
            text(
                f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}_test'"
            )
        )
        exists = result.scalar()

        if not exists:
            await conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}_test"))

    await postgres_engine.dispose()

    # Create engine for test database
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Async database session with transaction rollback for test isolation.

    Each test gets a fresh session in a transaction that rolls back after completion.
    This provides full isolation without recreating tables.
    """
    async with test_engine.connect() as connection:
        transaction: AsyncTransaction = await connection.begin()

        session_maker = async_sessionmaker(
            bind=connection, class_=AsyncSession, expire_on_commit=False
        )

        async with session_maker() as session:
            yield session

        await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing API endpoints.

    Database session dependency is automatically overridden to use test session.
    """

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> TestClient:
    """Synchronous test client for simple non-async/non-database tests."""
    return TestClient(app)
