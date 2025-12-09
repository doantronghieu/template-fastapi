"""Tests for _example extension services."""

import pytest

from app.extensions._example.schemas.api import (
    ExampleFeatureCreate,
    ExampleFeatureUpdate,
)
from app.extensions._example.service import ExampleFeatureService

pytestmark = pytest.mark.usefixtures("with_example_extension")


async def test_service_get_all(db_session):
    """Test service get_all method."""
    service = ExampleFeatureService(db_session)

    # Create some features
    await service.create(ExampleFeatureCreate(name="Feature 1", description="Desc 1"))
    await service.create(ExampleFeatureCreate(name="Feature 2", description="Desc 2"))

    # Get all
    features = await service.get_all()
    assert len(features) >= 2
    assert any(f.name == "Feature 1" for f in features)


async def test_service_create(db_session):
    """Test service create method."""
    service = ExampleFeatureService(db_session)

    data = ExampleFeatureCreate(
        name="New Feature", description="New description", is_active=True
    )
    feature = await service.create(data)

    assert feature.id is not None
    assert feature.name == "New Feature"
    assert feature.description == "New description"
    assert feature.is_active is True


async def test_service_get_by_id(db_session):
    """Test service get_by_id method."""
    service = ExampleFeatureService(db_session)

    # Create feature
    created = await service.create(
        ExampleFeatureCreate(name="Get By ID", description="Test")
    )

    # Get by ID
    feature = await service.get_by_id(created.id)
    assert feature is not None
    assert feature.id == created.id
    assert feature.name == "Get By ID"


async def test_service_get_by_id_not_found(db_session):
    """Test service get_by_id with nonexistent ID."""
    service = ExampleFeatureService(db_session)

    feature = await service.get_by_id(99999)
    assert feature is None


async def test_service_update(db_session):
    """Test service update method."""
    service = ExampleFeatureService(db_session)

    # Create feature
    created = await service.create(
        ExampleFeatureCreate(name="Original", description="Original desc")
    )

    # Update
    update_data = ExampleFeatureUpdate(description="Updated desc")
    updated = await service.update(created.id, update_data)

    assert updated is not None
    assert updated.id == created.id
    assert updated.name == "Original"  # Unchanged
    assert updated.description == "Updated desc"


async def test_service_delete(db_session):
    """Test service delete method."""
    service = ExampleFeatureService(db_session)

    # Create feature
    created = await service.create(
        ExampleFeatureCreate(name="To Delete", description="Will be deleted")
    )

    # Delete
    success = await service.delete(created.id)
    assert success is True

    # Verify deletion
    feature = await service.get_by_id(created.id)
    assert feature is None


async def test_service_delete_not_found(db_session):
    """Test service delete with nonexistent ID."""
    service = ExampleFeatureService(db_session)

    success = await service.delete(99999)
    assert success is False
