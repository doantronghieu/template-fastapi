"""Document conversion library with pluggable provider support.

Provides a unified interface for document-to-markdown conversion.
"""

from app.lib.documentation.base import DocumentConverter
from app.lib.documentation.dependencies import (
    DocumentConverterDep,
    get_document_converter,
)
from app.lib.documentation.schemas import ConversionMode, ConversionResult

__all__ = [
    # Protocol
    "DocumentConverter",
    # Schemas
    "ConversionMode",
    "ConversionResult",
    # Dependencies
    "get_document_converter",
    "DocumentConverterDep",
]
