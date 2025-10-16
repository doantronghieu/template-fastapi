"""Force drop all tables in the database.

This script is useful when alembic_version table is out of sync with actual database state.
It drops all tables including alembic_version to allow a clean migration from scratch.

WARNING: This will delete ALL data in the database!

Usage:
    python scripts/force_drop_all_tables.py          # Verbose output
    python scripts/force_drop_all_tables.py --quiet  # Minimal output (for Makefile)
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables (same as Alembic does)
load_dotenv()

# Import settings after loading .env
from app.core.config import settings  # noqa: E402


async def drop_all_tables(quiet: bool = False) -> None:
    """Drop all tables in the public schema.

    Args:
        quiet: If True, only print essential messages (for use in Makefile)
    """
    # Create engine from settings (same DATABASE_URL that Alembic uses)
    database_url = settings.DATABASE_URL

    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        # Get all tables
        result = await conn.execute(
            text(
                """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """
            )
        )
        tables = [row[0] for row in result.fetchall()]

        if not tables:
            if not quiet:
                print("No tables found in database.")
            return

        if not quiet:
            print(f"Found {len(tables)} tables to drop:")
            for table in tables:
                print(f"  - {table}")
            print("\nDropping all tables with CASCADE...")

        # Drop all tables with CASCADE to handle foreign key constraints
        for table in tables:
            await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            if not quiet:
                print(f"  ✓ Dropped {table}")

        if not quiet:
            print(f"\n✅ Successfully dropped all {len(tables)} tables.")
        else:
            print(f"✓ Dropped {len(tables)} tables")

    # Close engine
    await engine.dispose()


if __name__ == "__main__":
    quiet_mode = "--quiet" in sys.argv or "-q" in sys.argv
    asyncio.run(drop_all_tables(quiet=quiet_mode))
