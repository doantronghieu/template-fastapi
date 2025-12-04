"""LangChain integration for LLM provider.

Implements LLMProvider interface using LangChain's universal initialization.
"""

from fastapi import APIRouter


def setup_api(router: APIRouter) -> None:
    """Register LangChain API routes (if any needed in future)."""
    pass


def setup_webhooks(router: APIRouter) -> None:
    """Register LangChain webhook routes (if any needed in future)."""
    pass
