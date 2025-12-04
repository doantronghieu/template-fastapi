"""Core SQLAdmin views."""

from datetime import datetime

from sqladmin import ModelView
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from starlette.requests import Request

from app.models.example import Example


# Common formatter functions
def format_datetime(dt: datetime | None) -> str | None:
    """Format datetime to readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


class BaseAdmin(ModelView):
    """Base admin view with common configuration."""

    # Pagination - shared across all views
    page_size = 25
    page_size_options = [10, 25, 50, 100]

    def _build_details_query(self, request: Request, *options):
        """Helper to build details query with eager loaded relationships.

        Args:
            request: Starlette request object
            *options: SQLAlchemy loader options (can be relationship attributes or
                     already-configured selectinload chains)

        Returns:
            SQLAlchemy select statement with eager loading
        """
        pk = request.path_params["pk"]
        stmt = self._stmt_by_identifier(pk)

        if options:
            # Convert plain attributes to selectinload, pass through existing options
            processed_options = []
            for opt in options:
                # If it's a relationship attribute, wrap in selectinload
                if isinstance(opt, InstrumentedAttribute):
                    processed_options.append(selectinload(opt))
                else:
                    # Otherwise it's already a loader option, use as-is
                    processed_options.append(opt)

            stmt = stmt.options(*processed_options)

        return stmt


class ExampleAdmin(BaseAdmin, model=Example):
    """Admin view for Example model."""

    name = "Example"
    name_plural = "Examples"
    icon = "fa-solid fa-list"

    # List page configuration
    column_list = [Example.id, Example.name, Example.description, Example.created_at]
    column_searchable_list = [Example.name, Example.description]
    column_sortable_list = [Example.id, Example.name, Example.created_at]
    column_default_sort = [(Example.created_at, True)]

    # Form configuration
    form_columns = [Example.name, Example.description]

    # Details page
    column_details_list = [
        Example.id,
        Example.name,
        Example.description,
        Example.created_at,
        Example.updated_at,
    ]
