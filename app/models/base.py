"""Base model utilities for common patterns."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Field, SQLModel


def uuid_pk() -> Field:
    """Create a UUID primary key field.

    Returns:
        Field configured with UUID primary key
    """
    return Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )


def timestamp_field() -> Field:
    """Create a timezone-aware timestamp field.

    Returns:
        Field configured with UTC timestamp
    """
    return Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


def uuid_fk(table: str, *, nullable: bool = False, index: bool = True) -> Field:
    """Create a UUID foreign key field with optional index.

    Args:
        table: Target table name (e.g., "users")
        nullable: Whether the foreign key can be null
        index: Whether to create an index on this column

    Returns:
        Field configured with UUID foreign key
    """
    return Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey(f"{table}.id"),
            nullable=nullable,
            index=index,
        ),
    )


class BaseTable(SQLModel):
    """Base model with UUID primary key and timestamps."""

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PGUUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
    )
