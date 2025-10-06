"""Extension-specific test fixtures."""

import pytest

from app.core.config import settings


@pytest.fixture
def with_example_extension(monkeypatch):
    """Enable _example extension for tests."""
    monkeypatch.setattr(settings, "ENABLED_EXTENSIONS", ["_example"])
    yield
