"""Reusable filter utilities for SQLAdmin views."""

from collections.abc import Callable
from enum import Enum
from typing import Any

from sqlalchemy.sql.selectable import Select
from starlette.requests import Request


def enum_to_display_text(enum_member: Enum) -> str:
    """Convert enum name to display text.

    Transforms snake_case enum names to Title Case display text.

    Args:
        enum_member: The enum member to convert

    Returns:
        Human-readable display text
    """
    return enum_member.name.replace("_", " ").title()


class EnumFilterBase:
    """Base class for enum-based SQLAdmin filters.

    Automatically generates filter options from an enum class and handles
    query filtering. Subclasses only need to define class attributes.

    Attributes:
        title: Display title for the filter
        parameter_name: URL parameter name
        field: SQLAlchemy column to filter on
        enum_class: Enum class to generate options from
    """

    title: str
    parameter_name: str
    field: Any  # SQLAlchemy column descriptor
    enum_class: type[Enum]

    def lookups(
        self, _request: Request, _model: Any, _run_arbitrary_query: Callable[[Select], Any]
    ) -> list[tuple[str, str]]:
        """Generate filter options from enum class.

        Returns:
            List of (value, display_text) tuples for filter options
        """
        options = [("all", "All")]
        for member in self.enum_class:
            display_text = enum_to_display_text(member)
            options.append((member.value, display_text))
        return options

    async def get_filtered_query(
        self, query: Select, value: str, _model: Any
    ) -> Select:
        """Apply filter to query if value matches enum member.

        Args:
            query: SQLAlchemy select statement
            value: Filter value from URL parameter
            _model: SQLAlchemy model class (unused)

        Returns:
            Modified query with filter applied, or original query if no filter
        """
        if value and value != "all":
            # Validate value is a valid enum member
            try:
                self.enum_class(value)
                # Access field through class to avoid SQLAlchemy descriptor issues
                field = self.__class__.field
                return query.where(field == value)
            except ValueError:
                # Invalid enum value, return unfiltered query
                pass
        return query
