"""Docling integration for document conversion.

Implements DocumentConverter interface using Docling library.
"""

from fastapi import APIRouter


def setup_api(router: APIRouter) -> None:
    """Register Docling API routes (if any needed in future)."""
    pass


def setup_webhooks(router: APIRouter) -> None:
    """Register Docling webhook routes (if any needed in future)."""
    pass
