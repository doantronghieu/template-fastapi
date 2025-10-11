"""Serialization utilities for converting Python objects to API-compatible formats."""

from enum import Enum


def serialize_enum(value: str | Enum) -> str:
    """
    Serialize enum to string value.

    Handles both Enum instances and plain strings, making it safe to use
    on fields that might be either type (e.g., when enum constraints are
    enforced at the database level but not at the ORM level).

    Args:
        value: Enum instance or string

    Returns:
        String value

    Examples:
        >>> from enum import Enum
        >>> class Color(Enum):
        ...     RED = "red"
        >>> serialize_enum(Color.RED)
        'red'
        >>> serialize_enum("blue")
        'blue'
    """
    return value.value if isinstance(value, Enum) else value
