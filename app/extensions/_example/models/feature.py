"""Example feature model for demonstration."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class ExampleFeatureBase(SQLModel):
    """Base feature fields with descriptions."""

    name: str = Field(
        max_length=255, description="Feature name (1-255 characters, indexed)"
    )
    description: str | None = Field(
        default=None, max_length=500, description="Optional feature description"
    )
    is_active: bool = Field(default=True, description="Whether feature is active")


class ExampleFeature(ExampleFeatureBase, table=True):
    """Example feature model - demonstrates extension model structure.

    IMPORTANT: Table name must be prefixed with extension name to avoid conflicts.
    Pattern: {extension_name}_{table_name}
    """

    __tablename__ = "_example_features"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=255, index=True)  # Override to add index
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
