"""Core Models for database tables."""

from .base import BaseTable, timestamp_field, uuid_fk, uuid_pk
from .example import Example

__all__ = [
    "BaseTable",
    "Example",
    "timestamp_field",
    "uuid_fk",
    "uuid_pk",
]
