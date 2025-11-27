"""Docling document conversion library.

Converts PDF, DOCX, PPTX, XLSX, HTML, Markdown to Markdown output.
"""

from app.lib.docling.converter import DoclingConverter
from app.lib.docling.dependencies import DoclingConverterDep
from app.lib.docling.schemas import ConversionMode, ConversionResult

__all__ = [
    "DoclingConverter",
    "DoclingConverterDep",
    "ConversionMode",
    "ConversionResult",
]
