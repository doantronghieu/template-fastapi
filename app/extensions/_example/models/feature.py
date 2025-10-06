"""Example feature model for demonstration."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class ExampleFeature(SQLModel, table=True):
    """Example feature model - demonstrates extension model structure.

    IMPORTANT: Table name must be prefixed with extension name to avoid conflicts.
    Pattern: {extension_name}_{table_name}
    """

    __tablename__ = "_example_features"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
