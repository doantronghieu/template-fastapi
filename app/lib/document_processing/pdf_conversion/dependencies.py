"""PDF conversion dependency injection."""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.document_processing.pdf_conversion.base import PdfConverter
    from app.lib.document_processing.pdf_conversion.service import PdfConversionService


def get_pdf_converter_dependency() -> "PdfConverter":
    """Get PDF converter for dependency injection."""
    from app.lib.document_processing.pdf_conversion.factory import get_pdf_converter

    return get_pdf_converter()


def get_pdf_conversion_service_dependency() -> "PdfConversionService":
    """Get PDF conversion service for dependency injection."""
    from app.lib.document_processing.pdf_conversion.service import PdfConversionService

    return PdfConversionService()


PdfConverterDep = Annotated["PdfConverter", Depends(get_pdf_converter_dependency)]
PdfConversionServiceDep = Annotated[
    "PdfConversionService", Depends(get_pdf_conversion_service_dependency)
]
