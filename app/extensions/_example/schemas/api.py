"""Example feature schemas for API requests/responses."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..models import ExampleFeatureBase


class ExampleFeatureCreate(ExampleFeatureBase):
    """Schema for creating example features."""

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty (additional validation on inherited field)."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class ExampleFeatureUpdate(BaseModel):
    """Schema for updating example features.

    Note: Does not inherit from base because all fields are optional for partial updates.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class ExampleFeatureRead(ExampleFeatureBase):
    """Schema for reading example features."""

    id: int
    created_at: datetime
    updated_at: datetime
