"""PDF converter factory."""

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated

from app.lib.document_processing.pdf_conversion.schemas.dto import PdfConversionProvider

if TYPE_CHECKING:
    from app.lib.document_processing.pdf_conversion.base import PdfConverter


@lru_cache(maxsize=1)
def get_pdf_converter(
    provider: Annotated[
        PdfConversionProvider, "Provider to use"
    ] = PdfConversionProvider.WEASYPRINT,
) -> "PdfConverter":
    """Get cached PDF converter instance for provider."""
    providers = {
        PdfConversionProvider.WEASYPRINT: _get_weasyprint_converter,
    }
    return providers[provider]()


def _get_weasyprint_converter() -> "PdfConverter":
    """Get WeasyPrint PDF converter."""
    from app.lib.document_processing.pdf_conversion.providers.weasyprint import (
        WeasyPrintPdfConverter,
    )

    return WeasyPrintPdfConverter()
