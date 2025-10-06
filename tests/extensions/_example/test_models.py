"""Tests for _example extension models."""

import pytest
from sqlmodel import select

from app.extensions._example.models import ExampleFeature

pytestmark = pytest.mark.usefixtures("with_example_extension")


async def test_create_example_feature(db_session):
    """Test creating ExampleFeature model."""
    feature = ExampleFeature(
        name="Test Feature", description="Test description", is_active=True
    )
    db_session.add(feature)
    await db_session.commit()
    await db_session.refresh(feature)

    assert feature.id is not None
    assert feature.name == "Test Feature"
    assert feature.description == "Test description"
    assert feature.is_active is True
    assert feature.created_at is not None
    assert feature.updated_at is not None


async def test_query_example_features(db_session):
    """Test querying ExampleFeature models."""
    # Create multiple features
    features = [
        ExampleFeature(name=f"Feature {i}", description=f"Description {i}")
        for i in range(3)
    ]
    for feature in features:
        db_session.add(feature)
    await db_session.commit()

    # Query all features
    result = await db_session.execute(select(ExampleFeature))
    all_features = result.scalars().all()

    assert len(all_features) >= 3
    assert any(f.name == "Feature 0" for f in all_features)


async def test_update_example_feature(db_session):
    """Test updating ExampleFeature model."""
    feature = ExampleFeature(name="Original", description="Original description")
    db_session.add(feature)
    await db_session.commit()
    await db_session.refresh(feature)

    # Update
    feature.name = "Updated"
    feature.description = "Updated description"
    db_session.add(feature)
    await db_session.commit()
    await db_session.refresh(feature)

    assert feature.name == "Updated"
    assert feature.description == "Updated description"


async def test_delete_example_feature(db_session):
    """Test deleting ExampleFeature model."""
    feature = ExampleFeature(name="To Delete", description="Will be deleted")
    db_session.add(feature)
    await db_session.commit()
    await db_session.refresh(feature)
    feature_id = feature.id

    # Delete
    await db_session.delete(feature)
    await db_session.commit()

    # Verify deletion
    result = await db_session.get(ExampleFeature, feature_id)
    assert result is None
