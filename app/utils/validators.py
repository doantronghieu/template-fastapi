"""Validation utilities for data parsing and transformation.

Pure validator functions for common data validation patterns.
These are typically used as Pydantic field validators.
"""

from datetime import date


def parse_dd_mm_yyyy_date(value: str | date | None) -> date | None:
    """Parse DD/MM/YYYY date string to date object.

    Accepts date strings in DD/MM/YYYY format and converts them to Python
    date objects. Also accepts existing date objects and None values.

    Args:
        value: Date string in DD/MM/YYYY format, date object, or None

    Returns:
        Parsed date object or None

    Raises:
        ValueError: If string format is invalid

    Examples:
        >>> parse_dd_mm_yyyy_date("25/12/2024")
        date(2024, 12, 25)
        >>> parse_dd_mm_yyyy_date(date(2024, 12, 25))
        date(2024, 12, 25)
        >>> parse_dd_mm_yyyy_date(None)
        None

    Usage with Pydantic:
        @field_validator("date_field", mode="before")
        @classmethod
        def parse_date(cls, value: str | date | None) -> date | None:
            return parse_dd_mm_yyyy_date(value)
    """
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            day, month, year = value.split("/")
            return date(int(year), int(month), int(day))
        except (ValueError, AttributeError) as e:
            raise ValueError(
                f"Invalid date format. Expected DD/MM/YYYY, got: {value}"
            ) from e
    raise ValueError(f"Invalid date type: {type(value)}")
