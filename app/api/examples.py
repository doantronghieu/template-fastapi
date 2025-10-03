from fastapi import APIRouter

from app.models.example import Example
from app.services.example_service import ExampleServiceDep

router = APIRouter()


@router.get("/examples", response_model=list[Example])
async def get_examples(service: ExampleServiceDep):
    """Get all examples."""
    return await service.get_all()


@router.get("/examples/{example_id}", response_model=Example)
async def get_example(example_id: int, service: ExampleServiceDep):
    """Get example by ID."""
    return await service.get_by_id(example_id)
