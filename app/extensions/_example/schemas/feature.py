"""Example feature schemas for API requests/responses."""

from datetime import datetime

from pydantic import BaseModel, Field as PydanticField


class ExampleFeatureBase(BaseModel):
    """Base schema with common fields."""

    name: str = PydanticField(..., min_length=1)
    description: str | None = None
    is_active: bool = True


class ExampleFeatureCreate(ExampleFeatureBase):
    """Schema for creating example features."""

    pass


class ExampleFeatureUpdate(BaseModel):
    """Schema for updating example features."""

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ExampleFeatureRead(ExampleFeatureBase):
    """Schema for reading example features."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
