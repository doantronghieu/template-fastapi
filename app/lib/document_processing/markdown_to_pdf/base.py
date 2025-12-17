"""Markdown to PDF converter base class."""

from abc import ABC, abstractmethod
from typing import Annotated

from app.lib.document_processing.markdown_to_pdf.schemas.dto import (
    MarkdownToPdfOptions,
    MarkdownToPdfResult,
)


class MarkdownToPdfConverter(ABC):
    """Abstract base class for markdown to PDF conversion."""

    @abstractmethod
    def convert(
        self,
        markdown: Annotated[str, "Markdown content to convert"],
        options: Annotated[MarkdownToPdfOptions | None, "Conversion options"] = None,
    ) -> MarkdownToPdfResult:
        """Convert markdown string to PDF bytes."""
        ...
