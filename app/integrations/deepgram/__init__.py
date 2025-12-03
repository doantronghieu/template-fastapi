"""DeepGram integration for Speech-to-Text and Text-to-Speech.

Implements STTProvider and TTSProvider interfaces using DeepGram SDK.
"""

from fastapi import APIRouter


def setup_api(router: APIRouter) -> None:
    """Register DeepGram API routes (if any needed in future)."""
    pass


def setup_webhooks(router: APIRouter) -> None:
    """Register DeepGram webhook routes (if any needed in future)."""
    pass
