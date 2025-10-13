"""Example feature endpoints."""

from fastapi import APIRouter, HTTPException

from app.extensions._example.schemas.feature import (
    ExampleFeatureCreate,
    ExampleFeatureRead,
    ExampleFeatureUpdate,
)
from app.extensions._example.services import ExampleFeatureServiceDep

router = APIRouter(tags=["Example Features"])


@router.get("/features", response_model=list[ExampleFeatureRead])
async def list_features(service: ExampleFeatureServiceDep):
    """List all example features."""
    return await service.get_all()


@router.get("/features/{feature_id}", response_model=ExampleFeatureRead)
async def get_feature(feature_id: int, service: ExampleFeatureServiceDep):
    """Get example feature by ID."""
    feature = await service.get_by_id(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature


@router.post("/features", response_model=ExampleFeatureRead, status_code=201)
async def create_feature(data: ExampleFeatureCreate, service: ExampleFeatureServiceDep):
    """Create new example feature."""
    return await service.create(data)


@router.patch("/features/{feature_id}", response_model=ExampleFeatureRead)
async def update_feature(
    feature_id: int, data: ExampleFeatureUpdate, service: ExampleFeatureServiceDep
):
    """Update example feature."""
    feature = await service.update(feature_id, data)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature


@router.delete("/features/{feature_id}", status_code=204)
async def delete_feature(feature_id: int, service: ExampleFeatureServiceDep):
    """Delete example feature."""
    success = await service.delete(feature_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feature not found")
