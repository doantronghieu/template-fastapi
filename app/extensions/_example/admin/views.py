"""Example extension admin views."""

from sqladmin import ModelView

from app.extensions._example.models import ExampleFeature


class ExampleFeatureAdmin(ModelView, model=ExampleFeature):
    """Admin view for ExampleFeature model."""

    name = "Example Feature"
    name_plural = "Example Features"
    icon = "fa-solid fa-puzzle-piece"

    # List page configuration
    column_list = [
        ExampleFeature.id,
        ExampleFeature.name,
        ExampleFeature.description,
        ExampleFeature.is_active,
        ExampleFeature.created_at,
    ]
    column_searchable_list = [ExampleFeature.name, ExampleFeature.description]
    column_sortable_list = [
        ExampleFeature.id,
        ExampleFeature.name,
        ExampleFeature.created_at,
    ]
    column_default_sort = [(ExampleFeature.created_at, True)]

    # Form configuration
    form_columns = [
        ExampleFeature.name,
        ExampleFeature.description,
        ExampleFeature.is_active,
    ]

    # Details page
    column_details_list = [
        ExampleFeature.id,
        ExampleFeature.name,
        ExampleFeature.description,
        ExampleFeature.is_active,
        ExampleFeature.created_at,
        ExampleFeature.updated_at,
    ]

    # Pagination
    page_size = 25
    page_size_options = [10, 25, 50, 100]
