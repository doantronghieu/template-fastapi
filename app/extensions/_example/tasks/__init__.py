"""Example extension tasks."""

from app.utils.auto_import import auto_import

auto_import(__file__, "app.extensions._example.tasks")
