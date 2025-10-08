"""Shared schemas for library test endpoints."""

from app.api.lib.schemas.llm import CreateModelRequest, InvokeModelRequest

__all__ = [
    "CreateModelRequest",
    "InvokeModelRequest",
]
