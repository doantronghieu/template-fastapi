from sqlmodel import Field

from .base import BaseTable


class Example(BaseTable, table=True):
    """Example model demonstrating SQLModel setup."""

    __tablename__ = "examples"

    name: str = Field(
        index=True, max_length=255, description="Example name (indexed, max 255 chars)"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Optional example description"
    )
