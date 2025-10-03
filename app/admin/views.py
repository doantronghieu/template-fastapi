from sqladmin import ModelView

from app.models.example import Example


class ExampleAdmin(ModelView, model=Example):
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

    # Pagination
    page_size = 25
    page_size_options = [10, 25, 50, 100]
