"""Database Layer Configuration.

Dual-engine setup: async (asyncpg) for FastAPI endpoints, sync (psycopg2) for SQLAdmin.
Supabase-compatible with pgbouncer Session Pooler (statement_cache_size=0).

See docs/tech-stack.md for database configuration details.
See docs/architecture.md for session management and model patterns.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

# Async engine for FastAPI endpoints (asyncpg driver)
# Supabase compatibility: Disable prepared statement cache for pgbouncer Session Pooler
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    connect_args={"statement_cache_size": 0},
)

# Sync engine for SQLAdmin interface (psycopg2 driver)
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
)

# Async session factory with expire_on_commit=False
# Inject via SessionDep from app.core.dependencies
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
