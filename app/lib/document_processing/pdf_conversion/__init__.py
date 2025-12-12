"""PDF conversion module.

Provides markdown-to-PDF conversion using WeasyPrint + markdown-it-py.
"""

from app.lib.document_processing.pdf_conversion.base import PdfConverter
from app.lib.document_processing.pdf_conversion.dependencies import (
    PdfConversionServiceDep,
    PdfConverterDep,
    get_pdf_conversion_service_dependency,
    get_pdf_converter_dependency,
)
from app.lib.document_processing.pdf_conversion.factory import get_pdf_converter
from app.lib.document_processing.pdf_conversion.schemas.dto import (
    PdfConversionOptions,
    PdfConversionProvider,
    PdfConversionResult,
)
from app.lib.document_processing.pdf_conversion.service import PdfConversionService

__all__ = [
    # ABC
    "PdfConverter",
    # Service
    "PdfConversionService",
    # Schemas
    "PdfConversionOptions",
    "PdfConversionProvider",
    "PdfConversionResult",
    # Factory
    "get_pdf_converter",
    # Dependencies
    "get_pdf_converter_dependency",
    "get_pdf_conversion_service_dependency",
    "PdfConverterDep",
    "PdfConversionServiceDep",
]
