"""Example extension services."""

from .feature_service import (
    ExampleFeatureService,
    ExampleFeatureServiceDep,
    get_example_feature_service,
)

__all__ = [
    "ExampleFeatureService",
    "ExampleFeatureServiceDep",
    "get_example_feature_service",
]
