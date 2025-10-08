from datetime import datetime

from sqlmodel import Field, SQLModel


class Example(SQLModel, table=True):
    """Example model demonstrating SQLModel setup."""

    __tablename__ = "examples"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(
        index=True, max_length=255, description="Example name (indexed, max 255 chars)"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Optional example description"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when record was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when record was last updated",
    )
