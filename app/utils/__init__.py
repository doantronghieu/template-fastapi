"""General utility functions and helpers.

Standalone, reusable helper functions with minimal dependencies.
Pure functions and simple utilities used throughout the application.

Use this module for lightweight, independent helper functions that don't
require heavy dependencies or complex integrations.
"""

from .serialization import serialize_enum

__all__ = [
    "serialize_enum",
]
