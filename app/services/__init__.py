"""Core Service layer for business logic."""

from .base_crud import BaseCRUDService, PaginatedResponse, PaginationType
from .example_service import ExampleService, ExampleServiceDep, get_example_service

__all__ = [
    "BaseCRUDService",
    "PaginatedResponse",
    "PaginationType",
    "ExampleService",
    "ExampleServiceDep",
    "get_example_service",
]
